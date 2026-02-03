"""
Integration tests for workflows.
"""

import pytest
import asyncio
from unittest.mock import MagicMock, patch, AsyncMock

from src.workflows.triage import (
    classify_intent,
    get_required_agents,
    create_triage_agent,
    create_triage_workflow,
    INTENT_PATTERNS,
)
from src.workflows.parallel_analysis import (
    create_parallel_analysis_workflow,
    create_full_parallel_workflow,
)
from src.workflows.refinement import (
    create_refinement_agent,
    create_refinement_workflow,
    ContradictionResolver,
)
from src.workflows.orchestrator import (
    WorkbenchOrchestrator,
    create_orchestrator,
)
from src.tools.tool_registry import ToolRegistry


class TestTriageWorkflow:
    """Test triage workflow components."""

    def test_classify_variance_intent(self):
        """Test classification of variance-related triggers."""
        intent, confidence = classify_intent(
            "Explain why CPI dropped to 0.87 this month"
        )
        assert intent == "explain_variance"
        assert confidence > 0.3

    def test_classify_contract_intent(self):
        """Test classification of contract-related triggers."""
        intent, confidence = classify_intent(
            "Assess the impact of contract modification P00027"
        )
        assert intent == "assess_contract_change"
        assert confidence > 0.3

    def test_classify_quality_intent(self):
        """Test classification of quality-related triggers."""
        intent, confidence = classify_intent(
            "Investigate supplier quality escape affecting wing fasteners"
        )
        assert intent == "supplier_quality_investigation"
        assert confidence > 0.3

    def test_classify_risk_intent(self):
        """Test classification of risk-related triggers."""
        intent, confidence = classify_intent(
            "Assess program risk exposure and mitigation status"
        )
        assert intent == "risk_assessment"
        assert confidence > 0.3

    def test_classify_schedule_intent(self):
        """Test classification of schedule-related triggers."""
        intent, confidence = classify_intent(
            "Analyze milestone slip impact on critical path"
        )
        assert intent == "schedule_analysis"
        assert confidence > 0.3

    def test_classify_ambiguous_intent(self):
        """Test classification of ambiguous triggers defaults appropriately."""
        intent, confidence = classify_intent(
            "What is the status of the program?"
        )
        # Should return some valid intent with lower confidence
        assert intent in INTENT_PATTERNS.keys()
        assert 0 < confidence <= 1

    def test_get_required_agents_variance(self):
        """Test agent requirements for variance intent."""
        agents = get_required_agents("explain_variance")
        assert "cam_agent" in agents
        assert "pm_agent" in agents

    def test_get_required_agents_contract(self):
        """Test agent requirements for contract intent."""
        agents = get_required_agents("assess_contract_change")
        assert "contracts_agent" in agents
        assert "pm_agent" in agents

    def test_get_required_agents_unknown(self):
        """Test agent requirements for unknown intent."""
        agents = get_required_agents("unknown_intent")
        # Should return default agents
        assert len(agents) >= 2
        assert "pm_agent" in agents

    def test_create_triage_agent(self):
        """Test triage agent creation."""
        agent = create_triage_agent()
        assert agent.name == "triage_agent"
        assert len(agent.tools) == 0  # Triage doesn't need tools

    def test_create_triage_workflow(self):
        """Test triage workflow creation."""
        from google.adk.agents import SequentialAgent

        workflow = create_triage_workflow()
        assert workflow.name == "triage_workflow"
        assert isinstance(workflow, SequentialAgent)


class TestParallelAnalysisWorkflow:
    """Test parallel analysis workflow components."""

    def test_create_parallel_workflow_selected_agents(self):
        """Test creating parallel workflow with selected agents."""
        from google.adk.agents import ParallelAgent

        workflow = create_parallel_analysis_workflow(
            ["cam_agent", "risk_agent"]
        )
        assert workflow.name == "parallel_analysis_workflow"
        assert isinstance(workflow, ParallelAgent)
        assert len(workflow.sub_agents) == 2

    def test_create_parallel_workflow_excludes_pm(self):
        """Test that parallel workflow excludes PM agent."""
        workflow = create_parallel_analysis_workflow(
            ["cam_agent", "pm_agent", "risk_agent"]
        )
        agent_names = [a.name for a in workflow.sub_agents]
        # PM agent should not be in parallel analysis
        assert "pm_agent" not in agent_names

    def test_create_full_parallel_workflow(self):
        """Test creating full parallel workflow."""
        from google.adk.agents import ParallelAgent

        workflow = create_full_parallel_workflow()
        assert workflow.name == "full_parallel_analysis"
        assert isinstance(workflow, ParallelAgent)
        assert len(workflow.sub_agents) == 5  # All specialists except PM

    def test_parallel_workflow_fallback(self):
        """Test parallel workflow with no valid agents falls back."""
        workflow = create_parallel_analysis_workflow([])
        # Should have at least 2 default agents
        assert len(workflow.sub_agents) >= 2


class TestRefinementWorkflow:
    """Test refinement workflow components."""

    def test_create_refinement_agent(self):
        """Test refinement agent creation."""
        agent = create_refinement_agent()
        assert agent.name == "refinement_agent"

    def test_create_refinement_workflow(self):
        """Test refinement workflow creation."""
        from google.adk.agents import LoopAgent

        workflow = create_refinement_workflow(max_iterations=3)
        assert workflow.name == "refinement_workflow"
        assert isinstance(workflow, LoopAgent)
        assert workflow.max_iterations == 3

    def test_contradiction_resolver_initialization(self):
        """Test ContradictionResolver initialization."""
        resolver = ContradictionResolver(max_iterations=5)
        assert resolver.max_iterations == 5
        assert resolver.current_iteration == 0
        assert len(resolver.resolved_contradictions) == 0

    def test_contradiction_resolver_should_continue(self):
        """Test ContradictionResolver continuation logic."""
        resolver = ContradictionResolver(max_iterations=3)

        # First iteration with contradictions
        assert resolver.should_continue(2) is True
        assert resolver.current_iteration == 1

        # Second iteration
        assert resolver.should_continue(1) is True
        assert resolver.current_iteration == 2

        # Third iteration (max reached)
        assert resolver.should_continue(1) is False
        assert resolver.current_iteration == 3

    def test_contradiction_resolver_stops_when_resolved(self):
        """Test resolver stops when no contradictions remain."""
        resolver = ContradictionResolver(max_iterations=10)

        assert resolver.should_continue(0) is False

    def test_contradiction_resolver_record_resolution(self):
        """Test recording resolutions."""
        resolver = ContradictionResolver()
        resolver.current_iteration = 1

        resolver.record_resolution(
            contradiction_id="C-001",
            resolution="Agent A's finding is more credible",
            confidence="high"
        )

        assert "C-001" in resolver.resolved_contradictions
        assert len(resolver.resolution_history) == 1

    def test_contradiction_resolver_summary(self):
        """Test getting resolution summary."""
        resolver = ContradictionResolver()
        resolver.current_iteration = 2
        resolver.record_resolution("C-001", "Resolution 1", "high")

        summary = resolver.get_summary()

        assert summary["total_iterations"] == 2
        assert summary["resolved_count"] == 1
        assert "C-001" in summary["resolved_ids"]


class TestOrchestrator:
    """Test orchestrator functionality."""

    def test_create_orchestrator(self):
        """Test orchestrator creation via factory."""
        orchestrator = create_orchestrator()
        assert orchestrator is not None
        assert orchestrator.app_name == "program-execution-workbench"
        assert orchestrator.max_refinement_iterations == 3

    def test_create_orchestrator_custom_config(self):
        """Test orchestrator creation with custom config."""
        orchestrator = create_orchestrator(
            app_name="custom-app",
            max_refinement_iterations=5
        )
        assert orchestrator.app_name == "custom-app"
        assert orchestrator.max_refinement_iterations == 5

    def test_orchestrator_has_services(self):
        """Test orchestrator initializes all services."""
        orchestrator = create_orchestrator()

        assert orchestrator.registry is not None
        assert orchestrator.session_service is not None
        assert orchestrator.state_manager is not None
        assert orchestrator.contradiction_detector is not None
        assert orchestrator.tracer is not None
        assert orchestrator.metrics is not None

    @pytest.mark.asyncio
    async def test_orchestrator_run_basic(self):
        """Test basic orchestrator run."""
        orchestrator = create_orchestrator()

        result = await orchestrator.run(
            trigger="Explain CPI variance",
            user_id="test_user",
        )

        assert "case_file" in result
        assert "findings" in result
        assert "contradictions" in result
        assert "trace_id" in result
        assert result["case_file"]["intent"] == "explain_variance"

    @pytest.mark.asyncio
    async def test_orchestrator_run_contract_change(self):
        """Test orchestrator with contract change trigger."""
        orchestrator = create_orchestrator()

        result = await orchestrator.run(
            trigger="Assess contract modification P00027",
            user_id="test_user",
        )

        assert result["case_file"]["intent"] == "assess_contract_change"

    @pytest.mark.asyncio
    async def test_orchestrator_generates_leadership_brief(self):
        """Test that orchestrator generates a leadership brief."""
        orchestrator = create_orchestrator()

        result = await orchestrator.run(
            trigger="Investigate quality escape from supplier",
            user_id="test_user",
        )

        assert "leadership_brief" in result
        # Brief should contain the standard structure
        if result["leadership_brief"]:
            assert "WHAT HAPPENED" in result["leadership_brief"]


class TestWorkflowIntegration:
    """Integration tests for workflow pipeline."""

    @pytest.mark.asyncio
    async def test_full_workflow_variance_scenario(self):
        """Test complete workflow for variance scenario."""
        orchestrator = create_orchestrator()

        result = await orchestrator.run(
            trigger="""
            CPI has declined to 0.87 and SPI to 0.88.
            Wing Assembly milestone slipped 30 days.
            Explain the variance and recommend corrective actions.
            """,
            user_id="test_user",
        )

        # Verify all workflow phases completed
        assert result["case_file"]["intent"] == "explain_variance"
        assert len(result["findings"]) > 0
        assert result["trace_id"] is not None

    @pytest.mark.asyncio
    async def test_full_workflow_quality_escape(self):
        """Test complete workflow for quality escape scenario."""
        orchestrator = create_orchestrator()

        result = await orchestrator.run(
            trigger="""
            Quality escape detected: 240 defective fasteners from
            Apex Fastener Corp affecting 12 wing assemblies.
            Stop-ship issued. Conduct full investigation.
            """,
            user_id="test_user",
        )

        assert result["case_file"]["intent"] == "supplier_quality_investigation"
        # SQ agent should be included
        required_agents = result["case_file"]["required_agents"]
        assert "sq_agent" in required_agents
