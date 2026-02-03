"""
Tool registration and management for the Program Execution Workbench.

Provides a :class:`ToolRegistry` that wraps every workbench tool function in a
Google ADK :class:`~google.adk.tools.FunctionTool` and exposes helper methods
for retrieving tool sets by agent name, by individual tool name, or as a
complete collection.

Usage::

    from src.tools.tool_registry import ToolRegistry

    registry = ToolRegistry()

    # All tools available in the workbench
    all_tools = registry.get_all_tools()

    # Tools scoped for a specific agent
    pm_tools = registry.get_tools_for_agent("pm_agent")

    # Look up a single tool by name
    tool = registry.get_tool_by_name("read_evm_metrics")
"""

from __future__ import annotations

from typing import Callable, Dict, List, Optional

from google.adk.tools import FunctionTool

# ---------------------------------------------------------------------------
# Data tools  (read / fetch operations)
# ---------------------------------------------------------------------------
from src.tools.data_tools import (
    read_program_snapshot,
    read_evm_metrics,
    read_evm_history,
    read_ims_milestones,
    read_risk_register,
    read_contract_baseline,
    read_contract_mods,
    read_cdrl_list,
    read_supplier_metrics,
    read_quality_escape_data,
)

# ---------------------------------------------------------------------------
# Analysis tools  (compute / assess operations)
# ---------------------------------------------------------------------------
from src.tools.analysis_tools import (
    calculate_eac,
    calculate_variance_drivers,
    analyze_cpi_trend,
    calculate_risk_exposure,
    assess_supplier_risk,
    assess_contract_mod_impact,
    calculate_cost_of_poor_quality,
)

# ---------------------------------------------------------------------------
# Artifact tools  (document generation operations)
# ---------------------------------------------------------------------------
from src.tools.artifact_tools import (
    write_leadership_brief,
    write_cam_narrative,
    write_risk_register_update,
    write_action_items,
    write_eight_d_report,
    write_contract_change_summary,
)


# ---------------------------------------------------------------------------
# Agent-to-tool mapping
# ---------------------------------------------------------------------------

# Each entry maps an agent name to a list of the plain Python functions it is
# permitted to call.  The registry wraps each function in a FunctionTool at
# initialisation time and serves the wrapped versions via the public API.

_AGENT_TOOL_MAP: Dict[str, List[Callable]] = {
    "pm_agent": [
        # All artifact tools
        write_leadership_brief,
        write_cam_narrative,
        write_risk_register_update,
        write_action_items,
        write_eight_d_report,
        write_contract_change_summary,
        # Data & analysis tools relevant to PM oversight
        read_program_snapshot,
        read_evm_metrics,
        calculate_eac,
    ],
    "cam_agent": [
        read_evm_metrics,
        read_evm_history,
        read_ims_milestones,
        calculate_eac,
        calculate_variance_drivers,
        analyze_cpi_trend,
        write_cam_narrative,
        write_action_items,
    ],
    "rca_agent": [
        read_evm_metrics,
        read_ims_milestones,
        read_supplier_metrics,
        read_quality_escape_data,
        write_eight_d_report,
    ],
    "risk_agent": [
        read_risk_register,
        read_evm_metrics,
        read_supplier_metrics,
        calculate_risk_exposure,
        assess_supplier_risk,
        write_risk_register_update,
    ],
    "contracts_agent": [
        read_contract_baseline,
        read_contract_mods,
        read_cdrl_list,
        assess_contract_mod_impact,
        write_contract_change_summary,
    ],
    "sq_agent": [
        read_supplier_metrics,
        read_quality_escape_data,
        assess_supplier_risk,
        calculate_cost_of_poor_quality,
        write_action_items,
        write_eight_d_report,
    ],
}


class ToolRegistry:
    """Central registry that maps tool functions to ADK ``FunctionTool`` instances.

    On construction every unique callable referenced in the agent-tool map is
    wrapped once in a :class:`~google.adk.tools.FunctionTool`.  Subsequent
    look-ups return the same wrapper objects, ensuring consistent identity
    across agents that share tools.
    """

    def __init__(self) -> None:
        # Deduplicated mapping: function.__name__ -> FunctionTool
        self._tools: Dict[str, FunctionTool] = {}

        # Collect every unique function across all agents
        seen_functions: Dict[str, Callable] = {}
        for funcs in _AGENT_TOOL_MAP.values():
            for fn in funcs:
                if fn.__name__ not in seen_functions:
                    seen_functions[fn.__name__] = fn

        # Wrap each function exactly once
        for name, fn in seen_functions.items():
            self._tools[name] = FunctionTool(fn)

        # Pre-build per-agent FunctionTool lists for fast retrieval
        self._agent_tools: Dict[str, List[FunctionTool]] = {}
        for agent_name, funcs in _AGENT_TOOL_MAP.items():
            self._agent_tools[agent_name] = [
                self._tools[fn.__name__] for fn in funcs
            ]

    # -- public API ---------------------------------------------------------

    def get_tools_for_agent(self, agent_name: str) -> list[FunctionTool]:
        """Return the list of :class:`FunctionTool` instances assigned to *agent_name*.

        Parameters
        ----------
        agent_name:
            One of the recognised agent names (``"pm_agent"``,
            ``"cam_agent"``, ``"rca_agent"``, ``"risk_agent"``,
            ``"contracts_agent"``, ``"sq_agent"``).

        Returns
        -------
        list[FunctionTool]
            Ordered list of ``FunctionTool`` wrappers.  Returns an empty list
            if *agent_name* is not recognised.
        """
        return list(self._agent_tools.get(agent_name, []))

    def get_all_tools(self) -> list[FunctionTool]:
        """Return every registered :class:`FunctionTool` (deduplicated).

        Returns
        -------
        list[FunctionTool]
            All unique ``FunctionTool`` instances in the registry.
        """
        return list(self._tools.values())

    def get_tool_by_name(self, name: str) -> Optional[FunctionTool]:
        """Look up a single :class:`FunctionTool` by its function name.

        Parameters
        ----------
        name:
            The Python function name (e.g. ``"read_evm_metrics"``).

        Returns
        -------
        FunctionTool or None
            The matching tool, or ``None`` if no tool has that name.
        """
        return self._tools.get(name)

    # -- convenience --------------------------------------------------------

    @property
    def tool_names(self) -> list[str]:
        """Sorted list of all registered tool names."""
        return sorted(self._tools.keys())

    @property
    def agent_names(self) -> list[str]:
        """Sorted list of all recognised agent names."""
        return sorted(self._agent_tools.keys())

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<ToolRegistry tools={len(self._tools)} "
            f"agents={list(self._agent_tools.keys())}>"
        )
