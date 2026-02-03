"""
Data retrieval tools for the Program Execution Workbench.

Each function in this module reads from the mock data backends and returns
JSON-serializable dictionaries suitable for consumption by ADK FunctionTools.
All invocations are logged through the structured observability layer.

Usage with Google ADK::

    from google.adk import FunctionTool
    from src.tools.data_tools import read_program_snapshot, read_evm_metrics

    snapshot_tool = FunctionTool(read_program_snapshot)
    evm_tool = FunctionTool(read_evm_metrics)
"""

import copy
import time
from typing import Any, Dict

from src.mock_data.program_data import PROGRAM_SNAPSHOT
from src.mock_data.evm_data import EVM_METRICS, EVM_HISTORY
from src.mock_data.ims_data import IMS_MILESTONES, CRITICAL_PATH
from src.mock_data.risk_data import RISK_REGISTER, RISK_SUMMARY
from src.mock_data.contract_data import CONTRACT_BASELINE, CONTRACT_MODS, CDRL_LIST
from src.mock_data.supplier_data import (
    SUPPLIER_METRICS,
    QUALITY_ESCAPE_DATA,
)
from src.observability.logger import log_tool_call


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _safe_call(tool_name: str, params: Dict[str, Any], fn) -> dict:
    """Execute *fn*, log the call, and return the result or an error dict.

    Parameters
    ----------
    tool_name:
        Logical name of the tool (used in log records).
    params:
        Parameters dictionary passed through to the log.
    fn:
        Zero-argument callable that produces the tool result.
    """
    start = time.perf_counter()
    try:
        result = fn()
        elapsed_ms = (time.perf_counter() - start) * 1000
        log_tool_call("data_tools", tool_name, params, result, elapsed_ms)
        return result
    except Exception as exc:  # noqa: BLE001
        elapsed_ms = (time.perf_counter() - start) * 1000
        error_result = {"error": f"{type(exc).__name__}: {exc}"}
        log_tool_call("data_tools", tool_name, params, error_result, elapsed_ms)
        return error_result


# ---------------------------------------------------------------------------
# Public tool functions
# ---------------------------------------------------------------------------

def read_program_snapshot() -> dict:
    """Return the full program snapshot for the Advanced Fighter Program (AFP).

    The snapshot includes program metadata (contract number, prime contractor,
    contract type, program phase), the current reporting period, total budget,
    budget at completion, management reserve, undistributed budget, key
    personnel directory, and the Work Breakdown Structure (WBS) summary
    down to level 3.

    Returns
    -------
    dict
        A dictionary containing:
        - ``program_name``: Full program name.
        - ``contract_number``: DoD contract identifier.
        - ``contract_type``: Contract type (e.g. CPIF, FFP).
        - ``program_phase``: Current acquisition phase (e.g. EMD).
        - ``reporting_period``: Current reporting month.
        - ``total_budget``: Total program budget in USD.
        - ``budget_at_completion``: BAC in USD.
        - ``management_reserve``: MR remaining in USD.
        - ``undistributed_budget``: UB remaining in USD.
        - ``key_personnel``: Dict of key program personnel and contact info.
        - ``wbs_summary``: List of WBS elements with budgets and levels.
        - Other contract and classification metadata.
    """
    return _safe_call(
        "read_program_snapshot",
        {},
        lambda: copy.deepcopy(PROGRAM_SNAPSHOT),
    )


def read_evm_metrics() -> dict:
    """Return current Earned Value Management (EVM) performance metrics.

    Includes cumulative and period-specific EVM indices (CPI, SPI), dollar
    variances (CV, SV), earned value components (BCWP, BCWS, ACWP),
    at-completion projections (BAC, EAC, VAC, TCPI), and a work-package-level
    breakdown with individual CPI/SPI and variance explanations.

    Returns
    -------
    dict
        A dictionary containing:
        - ``CPI`` / ``SPI``: Cumulative performance indices.
        - ``CV`` / ``SV``: Cumulative cost and schedule variance in USD.
        - ``BCWP`` / ``BCWS`` / ``ACWP``: Earned value components in USD.
        - ``BAC`` / ``EAC`` / ``VAC``: At-completion values in USD.
        - ``TCPI``: To-Complete Performance Index (BAC-based).
        - ``work_packages``: List of work-package dicts with per-WBS metrics.
        - Period-specific metrics prefixed with ``period_``.
    """
    return _safe_call(
        "read_evm_metrics",
        {},
        lambda: copy.deepcopy(EVM_METRICS),
    )


def read_evm_history() -> dict:
    """Return EVM trending history for the last six reporting periods.

    Each record in the history contains cumulative BCWP, BCWS, ACWP, CPI,
    SPI, cost/schedule variance, Estimate at Completion (EAC), and a
    narrative summary for the period. This data supports trend analysis
    and identification of inflection points.

    Returns
    -------
    dict
        A dictionary containing:
        - ``periods``: List of monthly EVM snapshots ordered chronologically.
        - ``period_count``: Number of periods included.
        - ``earliest_period``: First period label in the history.
        - ``latest_period``: Most recent period label in the history.
    """
    def _build():
        history = copy.deepcopy(EVM_HISTORY)
        return {
            "periods": history,
            "period_count": len(history),
            "earliest_period": history[0]["period"] if history else None,
            "latest_period": history[-1]["period"] if history else None,
        }

    return _safe_call("read_evm_history", {}, _build)


def read_ims_milestones() -> dict:
    """Return all Integrated Master Schedule (IMS) milestones and critical path.

    Includes every tracked milestone with baseline date, forecast date,
    actual date (if completed), slip days, status, and notes. Also returns
    the critical path sequence, near-critical paths with remaining float,
    and overall schedule margin assessment.

    Returns
    -------
    dict
        A dictionary containing:
        - ``milestones``: List of milestone dicts with dates, status, slip.
        - ``milestone_count``: Total number of milestones.
        - ``critical_path``: Critical-path analysis dict with sequence,
          near-critical paths, and schedule margin.
        - ``completed_count``: Number of milestones completed.
        - ``at_risk_count``: Number of milestones at risk or slipped.
    """
    def _build():
        milestones = copy.deepcopy(IMS_MILESTONES)
        cp = copy.deepcopy(CRITICAL_PATH)
        completed = sum(1 for m in milestones if m["status"] == "completed")
        at_risk = sum(
            1 for m in milestones if m["status"] in ("at_risk", "slipped")
        )
        return {
            "milestones": milestones,
            "milestone_count": len(milestones),
            "critical_path": cp,
            "completed_count": completed,
            "at_risk_count": at_risk,
        }

    return _safe_call("read_ims_milestones", {}, _build)


def read_risk_register() -> dict:
    """Return the current program risk register and summary statistics.

    Each risk entry includes risk ID, title, category, probability, impact,
    risk score (5x5 matrix), status, owner, mitigation and contingency plans,
    affected milestones, and estimated cost and schedule impact.

    Returns
    -------
    dict
        A dictionary containing:
        - ``risks``: List of risk dicts with full detail.
        - ``summary``: Aggregate risk counts by level and status, plus total
          cost exposure.
    """
    def _build():
        return {
            "risks": copy.deepcopy(RISK_REGISTER),
            "summary": copy.deepcopy(RISK_SUMMARY),
        }

    return _safe_call("read_risk_register", {}, _build)


def read_contract_baseline() -> dict:
    """Return the contract baseline information for the AFP contract.

    Includes contract number, type, prime contractor, contracting and
    administering offices, award date, period of performance, original and
    current contract values, funded and unfunded balances, CPIF fee
    structure details (target cost/fee, share ratios, ceiling price),
    and CLIN summary.

    Returns
    -------
    dict
        A dictionary containing all contract baseline fields such as
        ``contract_number``, ``contract_type``, ``current_contract_value``,
        ``fee_structure``, ``clin_summary``, and EVMS applicability info.
    """
    return _safe_call(
        "read_contract_baseline",
        {},
        lambda: copy.deepcopy(CONTRACT_BASELINE),
    )


def read_contract_mods(mod_number: str = "") -> dict:
    """Return contract modifications, optionally filtered by mod number.

    When *mod_number* is provided (e.g. ``"P00027"``), only the matching
    modification is returned. When omitted or empty, all modifications are
    returned.

    Parameters
    ----------
    mod_number:
        Optional contract modification number to filter by (e.g. ``"P00027"``).
        Case-insensitive. Pass an empty string or omit to return all mods.

    Returns
    -------
    dict
        A dictionary containing:
        - ``mods``: List of contract modification dicts (filtered if applicable).
        - ``mod_count``: Number of mods returned.
        - ``filter_applied``: The mod_number filter value, or ``None`` if unfiltered.
    """
    def _build():
        mods = copy.deepcopy(CONTRACT_MODS)
        filter_val = mod_number.strip() if mod_number else None
        if filter_val:
            mods = [
                m for m in mods
                if m["mod_number"].upper() == filter_val.upper()
            ]
        return {
            "mods": mods,
            "mod_count": len(mods),
            "filter_applied": filter_val,
        }

    return _safe_call(
        "read_contract_mods",
        {"mod_number": mod_number},
        _build,
    )


def read_supplier_metrics(supplier_name: str = "") -> dict:
    """Return supplier performance metrics, optionally filtered by supplier name.

    When *supplier_name* is provided, only the matching supplier's data is
    returned (partial, case-insensitive match). When omitted or empty, all
    supplier metrics are returned.

    Each supplier record includes OTDP (on-time delivery performance), DPMO
    (defects per million opportunities), quality and delivery ratings,
    corrective action history, second-source availability, and status.

    Parameters
    ----------
    supplier_name:
        Optional supplier name to filter by (case-insensitive substring match).
        Pass an empty string or omit to return all suppliers.

    Returns
    -------
    dict
        A dictionary containing:
        - ``suppliers``: Dict mapping supplier names to their metric dicts,
          or a single supplier dict if filtered.
        - ``supplier_count``: Number of suppliers returned.
        - ``filter_applied``: The supplier_name filter value, or ``None``.
    """
    def _build():
        all_suppliers = copy.deepcopy(SUPPLIER_METRICS)
        filter_val = supplier_name.strip() if supplier_name else None
        if filter_val:
            filtered = {
                name: data
                for name, data in all_suppliers.items()
                if filter_val.lower() in name.lower()
            }
        else:
            filtered = all_suppliers
        return {
            "suppliers": filtered,
            "supplier_count": len(filtered),
            "filter_applied": filter_val,
        }

    return _safe_call(
        "read_supplier_metrics",
        {"supplier_name": supplier_name},
        _build,
    )


def read_quality_escape_data() -> dict:
    """Return quality escape event data for the current reporting period.

    Returns the full quality escape record including escape ID, severity,
    supplier involved, defective part details, units and assemblies affected,
    disposition, cost impact breakdown (rework labor, replacement material,
    NDI inspection, engineering disposition, schedule delay cost), schedule
    impact, affected milestones, containment actions, recovery plan, and
    lessons learned.

    Returns
    -------
    dict
        A dictionary containing all quality escape fields such as
        ``escape_id``, ``severity``, ``units_affected``, ``cost_impact``,
        ``recovery_plan``, ``containment_actions``, and ``lessons_learned``.
    """
    return _safe_call(
        "read_quality_escape_data",
        {},
        lambda: copy.deepcopy(QUALITY_ESCAPE_DATA),
    )


def read_cdrl_list() -> dict:
    """Return the Contract Data Requirements List (CDRL) for the AFP contract.

    Each CDRL entry includes the CDRL ID, DID number, title, submission
    frequency, distribution, classification, current status, last submission
    date, next due date, and any notes.

    Returns
    -------
    dict
        A dictionary containing:
        - ``cdrls``: List of CDRL entry dicts.
        - ``cdrl_count``: Total number of CDRLs.
        - ``current_count``: Number of CDRLs with status ``"current"``.
        - ``in_development_count``: Number of CDRLs in development.
    """
    def _build():
        cdrls = copy.deepcopy(CDRL_LIST)
        current = sum(1 for c in cdrls if c["status"] == "current")
        in_dev = sum(1 for c in cdrls if c["status"] == "in_development")
        return {
            "cdrls": cdrls,
            "cdrl_count": len(cdrls),
            "current_count": current,
            "in_development_count": in_dev,
        }

    return _safe_call("read_cdrl_list", {}, _build)
