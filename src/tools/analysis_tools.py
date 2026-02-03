"""
Analysis and computation tools for the Program Execution Workbench.

Each function in this module performs calculations or assessments against
the mock data backends and returns JSON-serializable dictionaries suitable
for consumption by ADK FunctionTools. All invocations are logged through
the structured observability layer.

Usage with Google ADK::

    from google.adk import FunctionTool
    from src.tools.analysis_tools import calculate_eac, assess_schedule_criticality

    eac_tool = FunctionTool(calculate_eac)
    sched_tool = FunctionTool(assess_schedule_criticality)
"""

import copy
import time
from typing import Any, Dict, List, Optional

from src.mock_data.evm_data import EVM_METRICS, EVM_HISTORY
from src.mock_data.ims_data import IMS_MILESTONES, CRITICAL_PATH
from src.mock_data.risk_data import RISK_REGISTER, RISK_SUMMARY
from src.mock_data.contract_data import CONTRACT_MODS, CONTRACT_BASELINE
from src.mock_data.supplier_data import SUPPLIER_METRICS, QUALITY_ESCAPE_DATA
from src.observability.logger import log_tool_call


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _safe_call(tool_name: str, params: Dict[str, Any], fn) -> dict:
    """Execute *fn*, log the call, and return the result or an error dict."""
    start = time.perf_counter()
    try:
        result = fn()
        elapsed_ms = (time.perf_counter() - start) * 1000
        log_tool_call("analysis_tools", tool_name, params, result, elapsed_ms)
        return result
    except Exception as exc:  # noqa: BLE001
        elapsed_ms = (time.perf_counter() - start) * 1000
        error_result = {"error": f"{type(exc).__name__}: {exc}"}
        log_tool_call("analysis_tools", tool_name, params, error_result, elapsed_ms)
        return error_result


# ---------------------------------------------------------------------------
# Public tool functions
# ---------------------------------------------------------------------------

def calculate_eac(method: str = "cpi") -> dict:
    """Calculate Estimate at Completion (EAC) using the specified method.

    Supports three EAC calculation methods commonly used in Earned Value
    Management:

    - **cpi**: ``EAC = BAC / CPI`` -- assumes future work will be performed
      at the same cost efficiency as cumulative to date.
    - **spi_cpi**: ``EAC = AC + (BAC - EV) / (CPI * SPI)`` -- composite
      method that accounts for both cost and schedule efficiency.
    - **management**: Returns the contractor's management estimate, which
      incorporates engineering judgment and recovery plans beyond purely
      index-based projections.

    Parameters
    ----------
    method:
        EAC calculation method. One of ``"cpi"``, ``"spi_cpi"``, or
        ``"management"``. Defaults to ``"cpi"``.

    Returns
    -------
    dict
        A dictionary containing:
        - ``eac``: The calculated EAC value in USD.
        - ``method``: The method label used.
        - ``method_description``: Human-readable explanation of the formula.
        - ``bac``: Budget at Completion used in the calculation.
        - ``cpi`` / ``spi``: Index values used (where applicable).
        - ``vac``: Variance at Completion (BAC - EAC).
        - ``vac_pct``: VAC as a percentage of BAC.
        - ``tcpi``: To-Complete Performance Index required to meet the
          calculated EAC.
    """
    def _build():
        m = method.strip().lower()
        bac = EVM_METRICS["BAC"]
        cpi = EVM_METRICS["CPI"]
        spi = EVM_METRICS["SPI"]
        acwp = EVM_METRICS["ACWP"]
        bcwp = EVM_METRICS["BCWP"]

        if m == "cpi":
            eac = bac / cpi
            desc = (
                "CPI-based EAC: EAC = BAC / CPI. Assumes remaining work "
                "will be performed at the same cumulative cost efficiency."
            )
        elif m in ("spi_cpi", "spi*cpi", "composite"):
            composite_index = cpi * spi
            eac = acwp + (bac - bcwp) / composite_index
            desc = (
                "SPI*CPI composite EAC: EAC = ACWP + (BAC - BCWP) / "
                "(CPI * SPI). Accounts for both cost and schedule "
                "inefficiency on remaining work."
            )
        elif m in ("management", "mgmt"):
            # Management estimate: take the reported EAC from the current
            # metrics and apply a small adjustment reflecting program office
            # engineering judgment (recovery plan credits).
            reported_eac = EVM_METRICS["EAC"]
            recovery_credit = 8_500_000  # management-assessed recovery savings
            eac = reported_eac - recovery_credit
            desc = (
                "Management EAC: Contractor-reported EAC adjusted for "
                "program office assessment of recovery plan feasibility. "
                "Includes $8.5M recovery credit for authorized overtime, "
                "parallel processing, and second-source activation."
            )
        else:
            return {
                "error": (
                    f"Unknown EAC method '{method}'. Supported methods: "
                    f"'cpi', 'spi_cpi', 'management'."
                )
            }

        vac = bac - eac
        vac_pct = (vac / bac) * 100 if bac else 0
        # TCPI against this EAC: remaining work / remaining funds
        remaining_work = bac - bcwp
        remaining_funds = eac - acwp
        tcpi_eac = remaining_work / remaining_funds if remaining_funds else None

        return {
            "eac": round(eac, 2),
            "method": m,
            "method_description": desc,
            "bac": bac,
            "cpi": cpi,
            "spi": spi,
            "acwp": acwp,
            "bcwp": bcwp,
            "vac": round(vac, 2),
            "vac_pct": round(vac_pct, 2),
            "tcpi_against_eac": round(tcpi_eac, 4) if tcpi_eac is not None else None,
        }

    return _safe_call("calculate_eac", {"method": method}, _build)


def assess_schedule_criticality(milestone_name: str) -> dict:
    """Assess schedule criticality for a named milestone.

    Searches the IMS for the milestone matching *milestone_name* (partial,
    case-insensitive match on the title) and returns slip days, overall
    impact assessment, whether the milestone is on the critical path, and
    which downstream milestones are affected.

    Parameters
    ----------
    milestone_name:
        Full or partial milestone title to search for (case-insensitive).

    Returns
    -------
    dict
        A dictionary containing:
        - ``milestone``: The matched milestone record.
        - ``slip_days``: Number of days the milestone has slipped.
        - ``is_critical_path``: Whether the milestone is on the critical path.
        - ``impact_assessment``: Textual assessment of criticality impact.
        - ``downstream_milestones``: List of downstream milestones affected
          by this milestone's slip.
        - ``risk_level``: Derived risk level (``"low"``, ``"medium"``,
          ``"high"``, ``"critical"``).
    """
    def _build():
        search = milestone_name.strip().lower()
        if not search:
            return {"error": "milestone_name is required."}

        # Find the milestone by partial title match
        match = None
        for m in IMS_MILESTONES:
            if search in m["title"].lower():
                match = copy.deepcopy(m)
                break

        if match is None:
            return {
                "error": (
                    f"No milestone found matching '{milestone_name}'. "
                    f"Available milestones: "
                    f"{[m['title'] for m in IMS_MILESTONES]}"
                )
            }

        slip = match["slip_days"]
        mid = match["milestone_id"]

        # Determine if this milestone is on the critical path
        cp_ids = [
            entry["milestone_id"]
            for entry in CRITICAL_PATH["critical_path_sequence"]
        ]
        is_cp = mid in cp_ids

        # Identify downstream milestones: milestones after this one in the
        # overall schedule that share the same WBS lineage or are on the
        # critical path after this node.
        downstream: List[dict] = []
        milestone_ids_ordered = [m["milestone_id"] for m in IMS_MILESTONES]
        if mid in milestone_ids_ordered:
            idx = milestone_ids_ordered.index(mid)
            for later in IMS_MILESTONES[idx + 1:]:
                later_copy = copy.deepcopy(later)
                # Check if downstream milestone is on critical path
                later_on_cp = later_copy["milestone_id"] in cp_ids
                # Estimate propagated slip: if this milestone is on the
                # critical path and the downstream is also on the path,
                # the slip propagates directly.
                propagated_slip = slip if (is_cp and later_on_cp) else 0
                if later_copy["status"] != "completed":
                    downstream.append({
                        "milestone_id": later_copy["milestone_id"],
                        "title": later_copy["title"],
                        "baseline_date": later_copy["baseline_date"],
                        "forecast_date": later_copy["forecast_date"],
                        "current_slip_days": later_copy["slip_days"],
                        "propagated_slip_days": propagated_slip,
                        "on_critical_path": later_on_cp,
                    })

        # Derive risk level from slip magnitude and critical-path membership
        if slip == 0:
            risk_level = "low"
            impact = "Milestone is on track with no schedule slip."
        elif slip <= 7 and not is_cp:
            risk_level = "low"
            impact = (
                f"Milestone has slipped {slip} day(s) but is not on the "
                f"critical path. Impact is contained within schedule float."
            )
        elif slip <= 14 or (slip <= 7 and is_cp):
            risk_level = "medium"
            impact = (
                f"Milestone has slipped {slip} day(s). "
                f"{'On the critical path -- slip directly impacts program end date. ' if is_cp else ''}"
                f"Downstream milestone(s) may be affected."
            )
        elif slip <= 30:
            risk_level = "high"
            impact = (
                f"Milestone has slipped {slip} day(s). "
                f"{'CRITICAL PATH: slip propagates directly to downstream milestones and program completion. ' if is_cp else ''}"
                f"Significant schedule recovery actions required."
            )
        else:
            risk_level = "critical"
            impact = (
                f"Milestone has slipped {slip} day(s), exceeding 30-day "
                f"threshold. "
                f"{'CRITICAL PATH: program end date is breached. ' if is_cp else ''}"
                f"Re-baseline or major recovery effort likely required."
            )

        return {
            "milestone": match,
            "slip_days": slip,
            "is_critical_path": is_cp,
            "impact_assessment": impact,
            "downstream_milestones": downstream,
            "downstream_count": len(downstream),
            "risk_level": risk_level,
        }

    return _safe_call(
        "assess_schedule_criticality",
        {"milestone_name": milestone_name},
        _build,
    )


def calculate_variance_drivers(threshold_percent: float = 5.0) -> dict:
    """Identify work packages driving cost and schedule variance beyond a threshold.

    Examines each work package in the current EVM data and flags those whose
    cost variance percentage (CV%) or schedule variance percentage (SV%)
    exceeds the given *threshold_percent*. Returns a ranked list of variance
    drivers sorted by total absolute variance.

    Parameters
    ----------
    threshold_percent:
        Minimum absolute variance percentage to flag a work package as a
        driver. Defaults to ``5.0`` (5%).

    Returns
    -------
    dict
        A dictionary containing:
        - ``threshold_percent``: The threshold used.
        - ``drivers``: Ranked list of work-package dicts that exceed the
          threshold, each with CV%, SV%, dollar variances, and explanation.
        - ``driver_count``: Number of drivers identified.
        - ``total_cv_from_drivers``: Sum of CV from flagged work packages.
        - ``total_sv_from_drivers``: Sum of SV from flagged work packages.
    """
    def _build():
        drivers: List[dict] = []

        for wp in EVM_METRICS["work_packages"]:
            bcwp = wp["BCWP"]
            bcws = wp["BCWS"]
            acwp = wp["ACWP"]

            cv = bcwp - acwp
            sv = bcwp - bcws
            cv_pct = (cv / bcwp * 100) if bcwp else 0
            sv_pct = (sv / bcws * 100) if bcws else 0

            # Check if either variance exceeds the threshold
            if abs(cv_pct) >= threshold_percent or abs(sv_pct) >= threshold_percent:
                drivers.append({
                    "wbs": wp["wbs"],
                    "title": wp["title"],
                    "cpi": wp["CPI"],
                    "spi": wp["SPI"],
                    "cv": cv,
                    "sv": sv,
                    "cv_pct": round(cv_pct, 2),
                    "sv_pct": round(sv_pct, 2),
                    "bac": wp["BAC"],
                    "eac": wp["EAC"],
                    "total_abs_variance": abs(cv) + abs(sv),
                    "status": wp["status"],
                    "variance_explanation": wp["variance_explanation"],
                })

        # Sort by total absolute variance descending (worst first)
        drivers.sort(key=lambda d: d["total_abs_variance"], reverse=True)

        total_cv = sum(d["cv"] for d in drivers)
        total_sv = sum(d["sv"] for d in drivers)

        return {
            "threshold_percent": threshold_percent,
            "drivers": drivers,
            "driver_count": len(drivers),
            "total_cv_from_drivers": total_cv,
            "total_sv_from_drivers": total_sv,
        }

    return _safe_call(
        "calculate_variance_drivers",
        {"threshold_percent": threshold_percent},
        _build,
    )


def calculate_risk_exposure() -> dict:
    """Calculate total risk exposure from the program risk register.

    Risk exposure for each risk is computed as:
    ``probability * cost_impact_estimate``. Returns a per-risk breakdown
    and an aggregate total, along with a weighted schedule exposure.

    Returns
    -------
    dict
        A dictionary containing:
        - ``risk_exposures``: List of dicts, one per risk, with risk_id,
          title, probability, cost_impact_estimate, calculated exposure,
          and schedule exposure in weighted days.
        - ``total_cost_exposure``: Sum of all individual risk exposures
          in USD.
        - ``total_weighted_schedule_days``: Sum of probability-weighted
          schedule impact days across all risks.
        - ``risk_count``: Number of risks evaluated.
        - ``top_exposure_risk``: The risk with the highest cost exposure.
    """
    def _build():
        exposures: List[dict] = []
        total_cost = 0.0
        total_sched = 0.0

        for risk in RISK_REGISTER:
            prob = risk["probability"]
            cost_est = risk["cost_impact_estimate"]
            sched_days = risk["schedule_impact_days"]

            cost_exposure = prob * cost_est
            sched_exposure = prob * sched_days

            total_cost += cost_exposure
            total_sched += sched_exposure

            exposures.append({
                "risk_id": risk["risk_id"],
                "title": risk["title"],
                "category": risk["category"],
                "risk_level": risk["risk_level"],
                "probability": prob,
                "cost_impact_estimate": cost_est,
                "cost_exposure": round(cost_exposure, 2),
                "schedule_impact_days": sched_days,
                "weighted_schedule_days": round(sched_exposure, 1),
                "status": risk["status"],
            })

        # Sort by cost exposure descending
        exposures.sort(key=lambda e: e["cost_exposure"], reverse=True)

        top_risk = exposures[0] if exposures else None

        return {
            "risk_exposures": exposures,
            "total_cost_exposure": round(total_cost, 2),
            "total_weighted_schedule_days": round(total_sched, 1),
            "risk_count": len(exposures),
            "top_exposure_risk": {
                "risk_id": top_risk["risk_id"],
                "title": top_risk["title"],
                "cost_exposure": top_risk["cost_exposure"],
            } if top_risk else None,
        }

    return _safe_call("calculate_risk_exposure", {}, _build)


def assess_supplier_risk(supplier_name: str) -> dict:
    """Assess overall supplier risk based on performance metrics.

    Evaluates the named supplier across multiple dimensions: on-time delivery
    performance (OTDP), quality (DPMO and quality rating), delivery trend,
    corrective action history, and second-source availability. Produces an
    overall risk level and actionable recommendations.

    Parameters
    ----------
    supplier_name:
        Supplier name to assess (case-insensitive substring match).

    Returns
    -------
    dict
        A dictionary containing:
        - ``supplier_name``: Matched supplier name.
        - ``overall_risk_level``: ``"low"``, ``"medium"``, ``"high"``, or
          ``"critical"``.
        - ``risk_score``: Numeric risk score (0-100, higher = more risk).
        - ``contributing_factors``: List of factor dicts describing each
          dimension's contribution to the overall risk.
        - ``open_corrective_actions``: Count of open CARs.
        - ``recommendations``: List of recommended actions.
    """
    def _build():
        search = supplier_name.strip().lower()
        if not search:
            return {"error": "supplier_name is required."}

        # Find supplier by partial match
        matched_name = None
        matched_data = None
        for name, data in SUPPLIER_METRICS.items():
            if search in name.lower():
                matched_name = name
                matched_data = copy.deepcopy(data)
                break

        if matched_data is None:
            return {
                "error": (
                    f"No supplier found matching '{supplier_name}'. "
                    f"Available suppliers: {list(SUPPLIER_METRICS.keys())}"
                )
            }

        factors: List[dict] = []
        risk_score = 0

        # --- OTDP assessment ---
        otdp = matched_data["otdp"]
        if otdp < 0.80:
            otdp_risk = "high"
            otdp_points = 25
            otdp_note = f"OTDP of {otdp:.0%} is critically below the 90% target."
        elif otdp < 0.90:
            otdp_risk = "medium"
            otdp_points = 15
            otdp_note = f"OTDP of {otdp:.0%} is below the 90% target."
        else:
            otdp_risk = "low"
            otdp_points = 5
            otdp_note = f"OTDP of {otdp:.0%} meets or exceeds the 90% target."
        risk_score += otdp_points
        factors.append({
            "dimension": "On-Time Delivery Performance",
            "value": otdp,
            "risk_level": otdp_risk,
            "points": otdp_points,
            "note": otdp_note,
        })

        # --- OTDP trend assessment ---
        trend = matched_data["otdp_trend"]
        if trend == "declining":
            trend_risk = "high"
            trend_points = 15
            trend_note = "Delivery performance is on a declining trend."
        elif trend == "stable":
            trend_risk = "low"
            trend_points = 5
            trend_note = "Delivery performance trend is stable."
        else:
            trend_risk = "low"
            trend_points = 0
            trend_note = f"Delivery performance trend: {trend}."
        risk_score += trend_points
        factors.append({
            "dimension": "Delivery Trend",
            "value": trend,
            "risk_level": trend_risk,
            "points": trend_points,
            "note": trend_note,
        })

        # --- Quality (DPMO) assessment ---
        dpmo = matched_data["dpmo"]
        benchmark = matched_data["dpmo_industry_benchmark"]
        if dpmo > benchmark * 3:
            quality_risk = "critical"
            quality_points = 25
            quality_note = (
                f"DPMO of {dpmo:,} is {dpmo / benchmark:.1f}x the industry "
                f"benchmark of {benchmark:,}."
            )
        elif dpmo > benchmark * 1.5:
            quality_risk = "medium"
            quality_points = 15
            quality_note = (
                f"DPMO of {dpmo:,} exceeds the industry benchmark of "
                f"{benchmark:,} by {((dpmo / benchmark) - 1) * 100:.0f}%."
            )
        elif dpmo > benchmark:
            quality_risk = "low"
            quality_points = 5
            quality_note = (
                f"DPMO of {dpmo:,} is slightly above the industry "
                f"benchmark of {benchmark:,}."
            )
        else:
            quality_risk = "low"
            quality_points = 0
            quality_note = (
                f"DPMO of {dpmo:,} is at or below the industry benchmark "
                f"of {benchmark:,}."
            )
        risk_score += quality_points
        factors.append({
            "dimension": "Quality (DPMO)",
            "value": dpmo,
            "benchmark": benchmark,
            "risk_level": quality_risk,
            "points": quality_points,
            "note": quality_note,
        })

        # --- Corrective actions assessment ---
        open_cars = [
            ca for ca in matched_data.get("corrective_actions", [])
            if ca["status"] == "open"
        ]
        critical_cars = [ca for ca in open_cars if ca["severity"] == "critical"]
        if critical_cars:
            car_risk = "critical"
            car_points = 20
            car_note = (
                f"{len(open_cars)} open CAR(s), including "
                f"{len(critical_cars)} critical-severity CAR(s)."
            )
        elif open_cars:
            car_risk = "medium"
            car_points = 10
            car_note = f"{len(open_cars)} open CAR(s), none critical severity."
        else:
            car_risk = "low"
            car_points = 0
            car_note = "No open corrective actions."
        risk_score += car_points
        factors.append({
            "dimension": "Corrective Actions",
            "open_count": len(open_cars),
            "critical_count": len(critical_cars),
            "risk_level": car_risk,
            "points": car_points,
            "note": car_note,
        })

        # --- Second source availability ---
        has_second = matched_data.get("second_source_available", False)
        if not has_second:
            ss_risk = "medium"
            ss_points = 10
            ss_note = "No qualified second source available; single-source dependency."
        else:
            ss_risk = "low"
            ss_points = 0
            ss_note = f"Second source available: {matched_data.get('second_source', 'N/A')}."
        risk_score += ss_points
        factors.append({
            "dimension": "Second Source Availability",
            "available": has_second,
            "second_source": matched_data.get("second_source"),
            "risk_level": ss_risk,
            "points": ss_points,
            "note": ss_note,
        })

        # --- Overall risk level ---
        if risk_score >= 70:
            overall = "critical"
        elif risk_score >= 45:
            overall = "high"
        elif risk_score >= 25:
            overall = "medium"
        else:
            overall = "low"

        # --- Recommendations ---
        recommendations: List[str] = []
        if otdp_risk in ("high", "medium"):
            recommendations.append(
                "Increase delivery monitoring frequency; consider weekly "
                "status calls and expedite reviews."
            )
        if quality_risk in ("critical", "high"):
            recommendations.append(
                "Mandate 100% source inspection for critical characteristics "
                "until DPMO falls below industry benchmark."
            )
        if trend == "declining":
            recommendations.append(
                "Conduct root-cause analysis on delivery trend decline; "
                "evaluate capacity and sub-tier performance."
            )
        if critical_cars:
            recommendations.append(
                "Escalate critical CAR(s) to supplier executive leadership; "
                "establish weekly corrective action review cadence."
            )
        if not has_second:
            recommendations.append(
                "Initiate second-source qualification to reduce single-source "
                "risk; evaluate candidates within 90 days."
            )
        if matched_data.get("status") == "probationary":
            recommendations.append(
                "Supplier is on probationary status. Maintain enhanced "
                "surveillance and consider performance improvement plan "
                "with contractual consequences."
            )
        if not recommendations:
            recommendations.append(
                "Supplier performance is satisfactory. Continue standard "
                "monitoring cadence."
            )

        return {
            "supplier_name": matched_name,
            "supplier_id": matched_data["supplier_id"],
            "status": matched_data["status"],
            "overall_risk_level": overall,
            "risk_score": risk_score,
            "risk_score_max": 100,
            "contributing_factors": factors,
            "open_corrective_actions": len(open_cars),
            "critical_corrective_actions": len(critical_cars),
            "recommendations": recommendations,
        }

    return _safe_call(
        "assess_supplier_risk",
        {"supplier_name": supplier_name},
        _build,
    )


def calculate_cost_of_poor_quality(event_type: str = "quality_escape") -> dict:
    """Calculate the Cost of Poor Quality (COPQ) from quality events.

    Currently supports the ``"quality_escape"`` event type, which draws data
    from the program's quality escape records. Returns a full breakdown of
    costs: rework labor, replacement material, inspection, engineering
    disposition, and schedule delay costs.

    Parameters
    ----------
    event_type:
        Type of quality event to analyse. Currently only
        ``"quality_escape"`` is supported. Defaults to ``"quality_escape"``.

    Returns
    -------
    dict
        A dictionary containing:
        - ``event_type``: The event type analysed.
        - ``event_id``: Identifier of the quality event.
        - ``breakdown``: Dict with itemised cost categories and amounts.
        - ``total_copq``: Total cost of poor quality in USD.
        - ``copq_as_pct_of_bac``: COPQ as a percentage of Budget at Completion.
        - ``schedule_impact_days``: Schedule days lost.
        - ``units_affected``: Number of defective units.
        - ``assemblies_affected``: Number of assemblies impacted.
        - ``root_cause_summary``: Brief root-cause statement.
    """
    def _build():
        etype = event_type.strip().lower()
        if etype != "quality_escape":
            return {
                "error": (
                    f"Unsupported event_type '{event_type}'. "
                    f"Currently supported: 'quality_escape'."
                )
            }

        qe = copy.deepcopy(QUALITY_ESCAPE_DATA)
        cost = qe["cost_impact"]
        bac = EVM_METRICS["BAC"]

        copq_pct = (cost["total"] / bac * 100) if bac else 0

        # Derive a root cause summary from the related CAR
        root_cause = (
            "Tier 2 forging die wear at Consolidated Metal Works not detected "
            "due to insufficient SPC monitoring. Apex Fastener Corp incoming "
            "inspection sampling plan was inadequate (AQL 1.0 Level II vs. "
            "required tightened inspection)."
        )

        return {
            "event_type": etype,
            "event_id": qe["escape_id"],
            "title": qe["title"],
            "severity": qe["severity"],
            "supplier": qe["supplier"],
            "breakdown": {
                "rework_labor": cost["rework_labor"],
                "replacement_material": cost["replacement_material"],
                "ndi_inspection": cost["ndi_inspection"],
                "engineering_disposition": cost["engineering_disposition"],
                "schedule_delay_cost": cost["schedule_delay_cost"],
            },
            "total_copq": cost["total"],
            "copq_as_pct_of_bac": round(copq_pct, 3),
            "bac": bac,
            "schedule_impact_days": qe["schedule_impact_days"],
            "units_affected": qe["units_affected"],
            "assemblies_affected": qe["assemblies_affected"],
            "milestones_affected": qe["milestones_affected"],
            "root_cause_summary": root_cause,
            "containment_actions": qe["containment_actions"],
            "recovery_plan": qe["recovery_plan"],
            "lessons_learned": qe["lessons_learned"],
        }

    return _safe_call(
        "calculate_cost_of_poor_quality",
        {"event_type": event_type},
        _build,
    )


def analyze_cpi_trend() -> dict:
    """Analyse CPI trend from EVM history to project future performance.

    Examines the six-month CPI history to determine the trend direction,
    average rate of change per period, and a simple linear projection of
    CPI at program completion. Also identifies if the trend has reached
    an inflection point or is accelerating.

    Returns
    -------
    dict
        A dictionary containing:
        - ``history``: List of period/CPI pairs from the EVM history.
        - ``current_cpi``: Most recent cumulative CPI.
        - ``trend_direction``: ``"declining"``, ``"improving"``, or ``"stable"``.
        - ``avg_cpi_change_per_period``: Average period-over-period CPI change.
        - ``recent_cpi_change``: Most recent period-over-period CPI change.
        - ``is_accelerating``: Whether the rate of decline/improvement is
          accelerating (True) or decelerating (False).
        - ``projected_cpi_at_completion``: Simple linear projection of CPI
          at program completion assuming the current trend continues.
        - ``periods_remaining``: Estimated number of monthly periods remaining.
        - ``assessment``: Textual interpretation of the trend.
    """
    def _build():
        history = EVM_HISTORY
        if len(history) < 2:
            return {"error": "Insufficient history data for trend analysis."}

        cpi_series = [(h["period"], h["CPI"]) for h in history]
        cpi_values = [c for _, c in cpi_series]

        # Calculate period-over-period changes
        changes = [
            cpi_values[i] - cpi_values[i - 1]
            for i in range(1, len(cpi_values))
        ]
        avg_change = sum(changes) / len(changes)
        recent_change = changes[-1]

        # Determine trend direction
        if avg_change < -0.005:
            direction = "declining"
        elif avg_change > 0.005:
            direction = "improving"
        else:
            direction = "stable"

        # Detect acceleration: is the rate of decline/improvement getting worse?
        if len(changes) >= 2:
            recent_delta = changes[-1] - changes[-2]
            # If declining and the change is becoming more negative, it's accelerating
            is_accelerating = (direction == "declining" and recent_delta < -0.002) or \
                              (direction == "improving" and recent_delta > 0.002)
        else:
            is_accelerating = False

        # Simple linear projection: estimate remaining periods and extrapolate
        # Program: Sep 2021 to Jun 2027 = ~69 months total
        # Current reporting period: Oct 2024 = ~37 months in
        # Remaining: ~32 months
        periods_remaining = 32
        projected_cpi = cpi_values[-1] + (avg_change * periods_remaining)
        # Bound the projection to reasonable limits
        projected_cpi = max(0.50, min(1.20, projected_cpi))

        current_cpi = cpi_values[-1]

        # Generate assessment
        if direction == "declining":
            if is_accelerating:
                assessment = (
                    f"CPI is declining and the rate of decline is accelerating. "
                    f"Current CPI of {current_cpi:.2f} has fallen from "
                    f"{cpi_values[0]:.2f} over {len(cpi_series)} periods "
                    f"(avg change: {avg_change:+.3f}/period). If the trend "
                    f"continues, CPI could reach {projected_cpi:.2f} at "
                    f"completion, significantly increasing the EAC. Immediate "
                    f"corrective action is recommended."
                )
            else:
                assessment = (
                    f"CPI is declining but the rate of decline appears to be "
                    f"stabilizing. Current CPI of {current_cpi:.2f} has fallen "
                    f"from {cpi_values[0]:.2f} over {len(cpi_series)} periods "
                    f"(avg change: {avg_change:+.3f}/period). Linear projection "
                    f"suggests CPI of {projected_cpi:.2f} at completion. "
                    f"Continued monitoring and variance analysis are warranted."
                )
        elif direction == "improving":
            assessment = (
                f"CPI is improving. Current CPI of {current_cpi:.2f} has "
                f"increased from {cpi_values[0]:.2f} (avg change: "
                f"{avg_change:+.3f}/period). Projected CPI at completion: "
                f"{projected_cpi:.2f}."
            )
        else:
            assessment = (
                f"CPI is relatively stable at {current_cpi:.2f} "
                f"(avg change: {avg_change:+.3f}/period). No significant "
                f"trend detected."
            )

        return {
            "history": cpi_series,
            "current_cpi": current_cpi,
            "trend_direction": direction,
            "avg_cpi_change_per_period": round(avg_change, 4),
            "recent_cpi_change": round(recent_change, 4),
            "is_accelerating": is_accelerating,
            "projected_cpi_at_completion": round(projected_cpi, 3),
            "periods_remaining": periods_remaining,
            "assessment": assessment,
        }

    return _safe_call("analyze_cpi_trend", {}, _build)


def assess_contract_mod_impact(mod_number: str) -> dict:
    """Assess the cost, schedule, and risk impact of a contract modification.

    Looks up the specified contract modification by number and analyses its
    impact on overall contract value, schedule, affected CLINs, and
    associated program risks.

    Parameters
    ----------
    mod_number:
        Contract modification number (e.g. ``"P00027"``). Case-insensitive.

    Returns
    -------
    dict
        A dictionary containing:
        - ``mod``: The full contract modification record.
        - ``cost_impact``: Cost impact in USD.
        - ``cost_impact_pct_of_baseline``: Cost impact as a percentage of the
          original contract value.
        - ``schedule_impact_weeks``: Schedule impact in weeks.
        - ``clins_affected``: List of CLINs affected by the modification.
        - ``cumulative_mod_value``: Total cost of all mods up to and
          including this one.
        - ``associated_risks``: List of related risk register entries.
        - ``assessment``: Textual impact assessment.
    """
    def _build():
        search = mod_number.strip().upper()
        if not search:
            return {"error": "mod_number is required."}

        # Find the mod
        matched_mod = None
        for mod in CONTRACT_MODS:
            if mod["mod_number"].upper() == search:
                matched_mod = copy.deepcopy(mod)
                break

        if matched_mod is None:
            available = [m["mod_number"] for m in CONTRACT_MODS]
            return {
                "error": (
                    f"No contract modification found with number '{mod_number}'. "
                    f"Available mods: {available}"
                )
            }

        original_value = CONTRACT_BASELINE["original_contract_value"]
        cost_impact = matched_mod["cost_impact"]
        cost_pct = (cost_impact / original_value * 100) if original_value else 0
        schedule_weeks = matched_mod["schedule_impact_weeks"]

        # Calculate cumulative mod value up to and including this mod
        cumulative = 0
        for mod in CONTRACT_MODS:
            cumulative += mod["cost_impact"]
            if mod["mod_number"].upper() == search:
                break

        # Find associated risks: look for risks that reference this mod
        # in their description or mitigation fields
        associated_risks: List[dict] = []
        mod_ref = matched_mod["mod_number"]
        for risk in RISK_REGISTER:
            risk_text = (
                risk["description"]
                + risk.get("mitigation", "")
                + risk.get("contingency", "")
            ).lower()
            if mod_ref.lower() in risk_text:
                associated_risks.append({
                    "risk_id": risk["risk_id"],
                    "title": risk["title"],
                    "risk_level": risk["risk_level"],
                    "cost_impact_estimate": risk["cost_impact_estimate"],
                })

        # Determine CLINs affected
        clins_affected = matched_mod.get("clins_affected", [])

        # Build assessment
        assessment_parts: List[str] = []

        if cost_impact == 0 and schedule_weeks == 0:
            assessment_parts.append(
                f"Mod {mod_ref} is administrative with no cost or schedule impact."
            )
        else:
            if cost_impact > 0:
                assessment_parts.append(
                    f"Mod {mod_ref} adds ${cost_impact:,.0f} to the contract "
                    f"value ({cost_pct:.2f}% of original baseline)."
                )
            if schedule_weeks > 0:
                assessment_parts.append(
                    f"Schedule impact of {schedule_weeks} week(s) "
                    f"({schedule_weeks * 7} calendar days)."
                )
            if clins_affected:
                assessment_parts.append(
                    f"Affects CLIN(s): {', '.join(clins_affected)}."
                )
            if associated_risks:
                risk_ids = [r["risk_id"] for r in associated_risks]
                assessment_parts.append(
                    f"Associated with program risk(s): {', '.join(risk_ids)}."
                )

        # Check for CDRLs added by this mod
        cdrl_added = matched_mod.get("cdrl_added")
        if cdrl_added:
            assessment_parts.append(
                f"New CDRL {cdrl_added} established by this modification."
            )

        assessment = " ".join(assessment_parts)

        return {
            "mod": matched_mod,
            "cost_impact": cost_impact,
            "cost_impact_pct_of_baseline": round(cost_pct, 2),
            "schedule_impact_weeks": schedule_weeks,
            "schedule_impact_days": schedule_weeks * 7,
            "original_contract_value": original_value,
            "new_contract_value": matched_mod["new_contract_value"],
            "clins_affected": clins_affected,
            "cumulative_mod_value": cumulative,
            "associated_risks": associated_risks,
            "associated_risk_count": len(associated_risks),
            "assessment": assessment,
        }

    return _safe_call(
        "assess_contract_mod_impact",
        {"mod_number": mod_number},
        _build,
    )
