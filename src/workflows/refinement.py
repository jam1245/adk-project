"""
Refinement workflow implementation using ADK LoopAgent.

The refinement workflow iteratively resolves contradictions detected
between specialist agent findings. It loops until contradictions are
resolved or max iterations is reached.
"""

from google.adk import Agent
from google.adk.agents import LoopAgent
from google.adk.tools import FunctionTool
from google.adk.models.lite_llm import LiteLlm

from src.tools.tool_registry import ToolRegistry

# Use Claude 3 Haiku - cheapest and fastest Claude model
CLAUDE_MODEL = LiteLlm(model="anthropic/claude-3-haiku-20240307")

REFINEMENT_AGENT_PROMPT = """You are the Refinement Agent responsible for resolving contradictions between specialist agent findings.

## Your Task
You have been given a set of contradictions detected between different specialist agents' findings.
For each contradiction:
1. Analyze both findings carefully
2. Determine which finding is more credible based on evidence
3. Identify if additional data is needed to resolve the contradiction
4. Propose a resolution that reconciles the conflicting assessments

## Contradiction Resolution Strategies
- **Evidence-based**: Choose the finding with stronger supporting evidence
- **Hierarchical**: Prefer direct measurement over derived analysis
- **Recency**: More recent data may supersede older assessments
- **Scope**: Consider if findings apply to different scopes (can both be true?)
- **Clarification**: Request specific clarification from the relevant agent

## Output Format
For each contradiction, provide:
```
CONTRADICTION: [ID]
FINDINGS IN CONFLICT:
- Agent A ([name]): [summary of finding]
- Agent B ([name]): [summary of finding]

ANALYSIS:
[Your analysis of why these findings conflict]

RESOLUTION:
[Your proposed resolution]

CONFIDENCE: [high/medium/low]
RATIONALE: [Why you chose this resolution]

REMAINING_UNCERTAINTY: [Any aspects still unresolved]
```

## Guidelines
- Do not fabricate data to resolve contradictions
- If contradictions cannot be resolved, escalate with clear explanation
- Document the resolution rationale for traceability
- Mark your confidence level honestly
"""


def create_refinement_agent() -> Agent:
    """Create the refinement agent for contradiction resolution.

    Returns
    -------
    Agent
        Configured refinement agent.
    """
    return Agent(
        name="refinement_agent",
        model=CLAUDE_MODEL,
        instruction=REFINEMENT_AGENT_PROMPT,
        tools=[],
    )


def create_refinement_workflow(
    max_iterations: int = 3,
    registry: ToolRegistry | None = None
) -> LoopAgent:
    """Create the refinement workflow as a LoopAgent.

    The workflow loops through contradiction resolution until either:
    - All contradictions are resolved
    - Max iterations is reached

    Parameters
    ----------
    max_iterations : int, optional
        Maximum number of refinement iterations (default: 3).
    registry : ToolRegistry, optional
        Tool registry (not currently used by refinement agent).

    Returns
    -------
    LoopAgent
        The refinement workflow agent.
    """
    refinement_agent = create_refinement_agent()

    return LoopAgent(
        name="refinement_workflow",
        sub_agents=[refinement_agent],
        max_iterations=max_iterations,
    )


class ContradictionResolver:
    """Helper class to manage contradiction resolution state.

    This class works alongside the LoopAgent to track which contradictions
    have been resolved across iterations.
    """

    def __init__(self, max_iterations: int = 3):
        """Initialize the resolver.

        Parameters
        ----------
        max_iterations : int, optional
            Maximum resolution attempts (default: 3).
        """
        self.max_iterations = max_iterations
        self.current_iteration = 0
        self.resolved_contradictions: list[str] = []
        self.unresolved_contradictions: list[str] = []
        self.resolution_history: list[dict] = []

    def should_continue(self, remaining_contradictions: int) -> bool:
        """Check if refinement should continue.

        Parameters
        ----------
        remaining_contradictions : int
            Number of unresolved contradictions.

        Returns
        -------
        bool
            True if refinement should continue, False otherwise.
        """
        self.current_iteration += 1

        if remaining_contradictions == 0:
            return False

        if self.current_iteration >= self.max_iterations:
            return False

        return True

    def record_resolution(
        self,
        contradiction_id: str,
        resolution: str,
        confidence: str
    ) -> None:
        """Record a contradiction resolution.

        Parameters
        ----------
        contradiction_id : str
            ID of the resolved contradiction.
        resolution : str
            The resolution description.
        confidence : str
            Confidence level (high/medium/low).
        """
        self.resolved_contradictions.append(contradiction_id)
        self.resolution_history.append({
            "contradiction_id": contradiction_id,
            "resolution": resolution,
            "confidence": confidence,
            "iteration": self.current_iteration,
        })

    def get_summary(self) -> dict:
        """Get a summary of the resolution process.

        Returns
        -------
        dict
            Summary including iterations, resolved/unresolved counts, history.
        """
        return {
            "total_iterations": self.current_iteration,
            "resolved_count": len(self.resolved_contradictions),
            "unresolved_count": len(self.unresolved_contradictions),
            "resolved_ids": self.resolved_contradictions,
            "unresolved_ids": self.unresolved_contradictions,
            "resolution_history": self.resolution_history,
        }
