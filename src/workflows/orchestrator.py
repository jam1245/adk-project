"""
Main workflow orchestrator for the Program Execution Workbench.

Coordinates the full analysis pipeline:
1. Triage: Classify intent and determine required agents
2. Parallel Analysis: Execute specialist agents concurrently
3. Refinement: Resolve contradictions iteratively
4. Synthesis: PM Agent consolidates findings into leadership outputs
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any, AsyncGenerator

from google.adk import Agent, Runner
from google.adk.sessions import InMemorySessionService, Session

from src.agents.pm_agent import create_pm_agent
from src.tools.tool_registry import ToolRegistry
from src.workflows.triage import (
    classify_intent,
    get_required_agents,
    create_triage_workflow,
)
from src.workflows.parallel_analysis import create_parallel_analysis_workflow
from src.workflows.refinement import (
    create_refinement_workflow,
    ContradictionResolver,
)
from src.contradiction.detector import ContradictionDetector
from src.state.models import (
    CaseFile,
    WorkbenchState,
    WorkbenchStatus,
    AgentOutput,
    Finding,
    FindingType,
)
from src.state.state_manager import StateManager
from src.observability.tracer import Tracer, ExecutionReport
from src.observability.metrics import MetricsCollector
from src.observability.logger import get_logger

logger = get_logger("orchestrator")


class WorkbenchOrchestrator:
    """Main orchestrator that coordinates the multi-agent workflow.

    The orchestrator manages the complete pipeline from intake to final
    output generation, handling state management, contradiction detection,
    and observability throughout.
    """

    def __init__(
        self,
        app_name: str = "program-execution-workbench",
        max_refinement_iterations: int = 3,
    ):
        """Initialize the orchestrator.

        Parameters
        ----------
        app_name : str, optional
            Application name for session management.
        max_refinement_iterations : int, optional
            Maximum iterations for contradiction resolution (default: 3).
        """
        self.app_name = app_name
        self.max_refinement_iterations = max_refinement_iterations

        # Core services
        self.registry = ToolRegistry()
        self.session_service = InMemorySessionService()
        self.state_manager = StateManager()
        self.contradiction_detector = ContradictionDetector()
        self.tracer = Tracer()
        self.metrics = MetricsCollector()

    async def run(
        self,
        trigger: str,
        user_id: str = "default_user",
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Run the complete workflow for a given trigger.

        Parameters
        ----------
        trigger : str
            The incoming request or trigger description.
        user_id : str, optional
            User identifier for session management.
        context : dict, optional
            Additional context data (EVM metrics, contract info, etc.).

        Returns
        -------
        dict
            Complete results including:
            - case_file: The created case file
            - findings: Aggregated findings from all agents
            - contradictions: Detected contradictions and resolutions
            - leadership_brief: Final synthesized brief (if generated)
            - artifacts: All generated artifacts
            - trace_id: Execution trace ID for debugging
        """
        # Start trace
        trace_id = self.tracer.start_trace(trigger[:100])
        logger.info(
            f"Starting orchestration for trigger: {trigger[:100]}...",
            trace_id=trace_id
        )

        try:
            # Phase 1: Triage
            triage_span = self.tracer.start_span(trace_id, "triage", "classify_intent")
            intent, confidence = classify_intent(trigger)
            required_agents = get_required_agents(intent)
            self.tracer.end_span(triage_span, "completed", {
                "intent": intent,
                "confidence": confidence,
                "required_agents": required_agents,
            })

            # Create case file
            case_file = CaseFile(
                intent=intent,
                trigger_description=trigger,
                program_name="Advanced Fighter Program (AFP)",
                reporting_period="October 2024",
                required_agents=required_agents,
            )

            # Initialize state
            state = WorkbenchState(
                case_file=case_file,
                status=WorkbenchStatus.triaging,
            )
            self.state_manager.save_state(state)

            logger.info(
                f"Triage complete: intent={intent}, agents={required_agents}",
                trace_id=trace_id
            )

            # Phase 2: Parallel Analysis
            state.status = WorkbenchStatus.analyzing
            self.state_manager.save_state(state)

            analysis_span = self.tracer.start_span(
                trace_id, "parallel_analysis", "execute_specialists"
            )

            # Filter out pm_agent for parallel phase (it runs in synthesis)
            parallel_agents = [a for a in required_agents if a != "pm_agent"]
            agent_outputs = await self._run_parallel_analysis(
                parallel_agents, trigger, user_id, trace_id
            )

            # Store agent outputs in state
            for agent_name, output in agent_outputs.items():
                state.agent_outputs[agent_name] = output

            self.tracer.end_span(analysis_span, "completed", {
                "agents_executed": list(agent_outputs.keys()),
                "total_findings": sum(len(o.findings) for o in agent_outputs.values()),
            })
            self.state_manager.save_state(state)

            # Phase 3: Contradiction Detection & Refinement
            state.status = WorkbenchStatus.refining
            self.state_manager.save_state(state)

            refinement_span = self.tracer.start_span(
                trace_id, "refinement", "resolve_contradictions"
            )

            contradictions = self.contradiction_detector.detect(state.agent_outputs)
            state.contradictions = contradictions

            if contradictions:
                logger.info(
                    f"Detected {len(contradictions)} contradictions, starting refinement",
                    trace_id=trace_id
                )
                resolver = ContradictionResolver(self.max_refinement_iterations)
                # In a full implementation, we would loop with the refinement agent
                # For now, we just detect and log contradictions
                for c in contradictions:
                    resolution = self.contradiction_detector.suggest_resolution(c)
                    c.resolution = resolution

            self.tracer.end_span(refinement_span, "completed", {
                "contradictions_found": len(contradictions),
                "contradictions_resolved": sum(1 for c in contradictions if c.resolution),
            })
            self.state_manager.save_state(state)

            # Phase 4: Synthesis
            state.status = WorkbenchStatus.synthesizing
            self.state_manager.save_state(state)

            synthesis_span = self.tracer.start_span(
                trace_id, "pm_agent", "synthesize_findings"
            )

            synthesis_result = await self._run_synthesis(
                state, trigger, user_id, trace_id
            )

            state.leadership_brief = synthesis_result.get("leadership_brief")
            state.artifacts.update(synthesis_result.get("artifacts", {}))

            self.tracer.end_span(synthesis_span, "completed", {
                "brief_generated": bool(state.leadership_brief),
                "artifacts_count": len(state.artifacts),
            })

            # Complete
            state.status = WorkbenchStatus.complete
            self.state_manager.save_state(state)
            self.tracer.end_trace(trace_id, "completed")

            # Generate execution report
            trace_data = self.tracer.get_trace(trace_id)
            report = ExecutionReport(trace_data)

            logger.info(
                f"Orchestration complete: {len(state.agent_outputs)} agents, "
                f"{len(contradictions)} contradictions",
                trace_id=trace_id
            )

            return {
                "case_file": case_file.model_dump(),
                "findings": {
                    name: output.model_dump()
                    for name, output in state.agent_outputs.items()
                },
                "contradictions": [c.model_dump() for c in state.contradictions],
                "leadership_brief": state.leadership_brief,
                "artifacts": state.artifacts,
                "trace_id": trace_id,
                "execution_report": report.render(),
            }

        except Exception as e:
            logger.error(f"Orchestration failed: {e}", trace_id=trace_id)
            self.tracer.end_trace(trace_id, "error")
            raise

    async def _run_parallel_analysis(
        self,
        agent_names: list[str],
        trigger: str,
        user_id: str,
        trace_id: str,
    ) -> dict[str, AgentOutput]:
        """Execute specialist agents in parallel.

        Parameters
        ----------
        agent_names : list[str]
            Names of agents to execute.
        trigger : str
            The trigger/request text.
        user_id : str
            User identifier.
        trace_id : str
            Trace ID for observability.

        Returns
        -------
        dict[str, AgentOutput]
            Mapping of agent names to their outputs.
        """
        outputs = {}

        # Create parallel workflow
        parallel_workflow = create_parallel_analysis_workflow(
            agent_names, self.registry
        )

        # Create runner for parallel workflow
        runner = Runner(
            app_name=self.app_name,
            agent=parallel_workflow,
            session_service=self.session_service,
        )

        # Create session
        session = await self.session_service.create_session(
            app_name=self.app_name,
            user_id=user_id,
        )

        # Add trigger to session state
        session.state["trigger"] = trigger
        session.state["trace_id"] = trace_id

        # For demo purposes, create simulated outputs
        # In production, this would run the actual agents
        for agent_name in agent_names:
            start_time = datetime.now(timezone.utc)
            outputs[agent_name] = AgentOutput(
                agent_name=agent_name,
                findings=[
                    Finding(
                        agent_name=agent_name,
                        finding_type=FindingType.analysis,
                        content=f"Analysis from {agent_name} for: {trigger[:50]}...",
                        confidence=0.85,
                        evidence_refs=["mock_data"],
                    )
                ],
                overall_confidence=0.85,
                execution_time_ms=150,
                tool_calls_made=3,
                errors=[],
            )

        return outputs

    async def _run_synthesis(
        self,
        state: WorkbenchState,
        trigger: str,
        user_id: str,
        trace_id: str,
    ) -> dict[str, Any]:
        """Run the PM Agent to synthesize findings.

        Parameters
        ----------
        state : WorkbenchState
            Current workbench state with all findings.
        trigger : str
            Original trigger text.
        user_id : str
            User identifier.
        trace_id : str
            Trace ID for observability.

        Returns
        -------
        dict
            Synthesis results including leadership_brief and artifacts.
        """
        pm_agent = create_pm_agent(self.registry)

        runner = Runner(
            app_name=self.app_name,
            agent=pm_agent,
            session_service=self.session_service,
        )

        session = await self.session_service.create_session(
            app_name=self.app_name,
            user_id=user_id,
        )

        # Prepare context for PM agent
        findings_summary = []
        for agent_name, output in state.agent_outputs.items():
            for finding in output.findings:
                findings_summary.append(
                    f"[{agent_name}] ({finding.finding_type.value}): {finding.content}"
                )

        session.state["trigger"] = trigger
        session.state["findings"] = findings_summary
        session.state["contradictions"] = [
            c.model_dump() for c in state.contradictions
        ]

        # For demo, return simulated synthesis
        brief = f"""# Leadership Brief: {state.case_file.intent.replace('_', ' ').title()}

**Program:** {state.case_file.program_name}
**Period:** {state.case_file.reporting_period}
**Generated:** {datetime.now(timezone.utc).isoformat()}

## WHAT HAPPENED
{trigger}

## WHY IT HAPPENED
Based on analysis from {len(state.agent_outputs)} specialist agents:
{chr(10).join(f'- {f}' for f in findings_summary[:3])}

## SO WHAT
This situation requires management attention. {len(state.contradictions)} areas require clarification.

## NOW WHAT
1. Review detailed findings from specialist agents
2. Address identified contradictions
3. Implement recommended corrective actions
"""

        return {
            "leadership_brief": brief,
            "artifacts": {
                "brief_generated_at": datetime.now(timezone.utc).isoformat(),
            },
        }


def create_orchestrator(
    app_name: str = "program-execution-workbench",
    max_refinement_iterations: int = 3,
) -> WorkbenchOrchestrator:
    """Factory function to create a configured orchestrator.

    Parameters
    ----------
    app_name : str, optional
        Application name for session management.
    max_refinement_iterations : int, optional
        Maximum iterations for contradiction resolution.

    Returns
    -------
    WorkbenchOrchestrator
        Configured orchestrator instance.
    """
    return WorkbenchOrchestrator(
        app_name=app_name,
        max_refinement_iterations=max_refinement_iterations,
    )
