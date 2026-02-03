"""
Parallel analysis workflow implementation using ADK ParallelAgent.

The parallel analysis workflow executes multiple specialist agents
concurrently to gather findings from different perspectives.
"""

from google.adk.agents import ParallelAgent

from src.agents.cam_agent import create_cam_agent
from src.agents.rca_agent import create_rca_agent
from src.agents.risk_agent import create_risk_agent
from src.agents.contracts_agent import create_contracts_agent
from src.agents.sq_agent import create_sq_agent
from src.tools.tool_registry import ToolRegistry


def create_parallel_analysis_workflow(
    required_agents: list[str],
    registry: ToolRegistry | None = None
) -> ParallelAgent:
    """Create a parallel analysis workflow with the specified agents.

    Parameters
    ----------
    required_agents : list[str]
        List of agent names to include in parallel execution.
        Valid values: cam_agent, rca_agent, risk_agent, contracts_agent, sq_agent
        Note: pm_agent is excluded from parallel analysis as it runs in synthesis.
    registry : ToolRegistry, optional
        Tool registry for agent creation. If not provided, a new one is created.

    Returns
    -------
    ParallelAgent
        A ParallelAgent that will execute the specified specialist agents
        concurrently.

    Example
    -------
    >>> workflow = create_parallel_analysis_workflow(
    ...     ["cam_agent", "rca_agent", "risk_agent"]
    ... )
    """
    if registry is None:
        registry = ToolRegistry()

    # Map agent names to creation functions
    agent_creators = {
        "cam_agent": create_cam_agent,
        "rca_agent": create_rca_agent,
        "risk_agent": create_risk_agent,
        "contracts_agent": create_contracts_agent,
        "sq_agent": create_sq_agent,
    }

    # Create only the requested agents (excluding pm_agent for parallel phase)
    sub_agents = []
    for agent_name in required_agents:
        if agent_name in agent_creators:
            sub_agents.append(agent_creators[agent_name](registry))

    if not sub_agents:
        # Fallback: at minimum include CAM and Risk agents
        sub_agents = [
            create_cam_agent(registry),
            create_risk_agent(registry),
        ]

    return ParallelAgent(
        name="parallel_analysis_workflow",
        sub_agents=sub_agents,
    )


def create_full_parallel_workflow(registry: ToolRegistry | None = None) -> ParallelAgent:
    """Create a parallel workflow with all specialist agents.

    This is a convenience function for scenarios requiring comprehensive
    analysis from all specialist perspectives.

    Parameters
    ----------
    registry : ToolRegistry, optional
        Tool registry for agent creation.

    Returns
    -------
    ParallelAgent
        A ParallelAgent with all five specialist agents.
    """
    if registry is None:
        registry = ToolRegistry()

    return ParallelAgent(
        name="full_parallel_analysis",
        sub_agents=[
            create_cam_agent(registry),
            create_rca_agent(registry),
            create_risk_agent(registry),
            create_contracts_agent(registry),
            create_sq_agent(registry),
        ],
    )
