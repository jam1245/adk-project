"""
Scenario 1: Explain Variance with CPI/SPI Drift + Schedule Slip

This scenario demonstrates the workbench handling a variance explanation
request triggered by significant EVM threshold breaches.

Setup:
- Program: Advanced Fighter Program (AFP)
- Reporting Period: October 2024
- EVM Metrics: CPI = 0.87, SPI = 0.88, CV = -$2.1M, SV = -$1.8M
- IMS: Key milestone "Wing Assembly Complete" slipped 30 days
- Trigger: Significant variance threshold breached
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone

# Scenario configuration
SCENARIO_NAME = "variance_explanation"
SCENARIO_TITLE = "Explain Variance with CPI/SPI Drift + Schedule Slip"

SCENARIO_TRIGGER = """
VARIANCE REPORT ALERT - October 2024

Program: Advanced Fighter Program (AFP)
Contract: FA8611-21-C-0042

THRESHOLD BREACH DETECTED:
- Cost Performance Index (CPI): 0.87 (threshold: 0.90)
- Schedule Performance Index (SPI): 0.88 (threshold: 0.90)
- Cumulative Cost Variance (CV): -$2,100,000
- Cumulative Schedule Variance (SV): -$1,800,000

MILESTONE ALERT:
- "Wing Assembly Complete" has slipped 30 days from baseline
- Critical path impact detected

REQUEST: Provide comprehensive variance explanation with root cause analysis,
risk assessment, and recommended corrective actions for leadership review.
"""

EXPECTED_AGENTS = [
    "cam_agent",      # EVM analysis, variance drivers
    "rca_agent",      # Root cause analysis (5 Whys)
    "sq_agent",       # Supplier quality assessment
    "risk_agent",     # Risk escalation assessment
    "pm_agent",       # Leadership brief synthesis
]

EXPECTED_OUTPUTS = {
    "leadership_brief": {
        "format": "markdown",
        "sections": ["WHAT HAPPENED", "WHY IT HAPPENED", "SO WHAT", "NOW WHAT"],
    },
    "cam_narrative": {
        "wbs": "1.3.2",
        "name": "Wing Assembly",
        "expected_variance_type": "unfavorable cost and schedule",
    },
    "risk_register_updates": {
        "risks_to_update": ["R-001", "R-002"],
        "expected_severity_change": "escalated",
    },
    "action_items": {
        "min_count": 3,
        "expected_categories": ["supplier", "recovery", "governance"],
    },
}


def get_scenario_context() -> dict:
    """Get the context data for this scenario.

    Returns
    -------
    dict
        Context including EVM metrics, milestones, and supplier data
        relevant to this scenario.
    """
    return {
        "program_name": "Advanced Fighter Program (AFP)",
        "reporting_period": "October 2024",
        "evm_metrics": {
            "CPI": 0.87,
            "SPI": 0.88,
            "CV": -2_100_000,
            "SV": -1_800_000,
            "variance_drivers": [
                {
                    "wbs_id": "1.3.2",
                    "wbs_name": "Wing Assembly",
                    "cpi": 0.72,
                    "cv_contribution": -1_650_000,
                }
            ],
        },
        "milestones": {
            "critical_slip": {
                "name": "Wing Assembly Complete",
                "slip_days": 30,
                "impact": "Critical path affected",
            }
        },
        "supplier_issues": {
            "primary_supplier": "Apex Fastener Corp",
            "otdp": 72,
            "dpmo": 8500,
            "quality_escapes": 3,
        },
    }


async def run_scenario(orchestrator) -> dict:
    """Execute the variance explanation scenario.

    Parameters
    ----------
    orchestrator : WorkbenchOrchestrator
        The orchestrator instance to use.

    Returns
    -------
    dict
        Complete scenario results.
    """
    print(f"\n{'='*60}")
    print(f"SCENARIO 1: {SCENARIO_TITLE}")
    print(f"{'='*60}\n")

    print("Trigger:")
    print("-" * 40)
    print(SCENARIO_TRIGGER[:500] + "...")
    print()

    print("Executing workflow...")
    result = await orchestrator.run(
        trigger=SCENARIO_TRIGGER,
        user_id="demo_user",
        context=get_scenario_context(),
    )

    print("\n" + "="*60)
    print("SCENARIO 1 COMPLETE")
    print("="*60)

    return result


def validate_outputs(result: dict) -> dict:
    """Validate that scenario outputs meet expectations.

    Parameters
    ----------
    result : dict
        The scenario execution result.

    Returns
    -------
    dict
        Validation results with pass/fail status for each check.
    """
    validations = {}

    # Check leadership brief was generated
    validations["leadership_brief_generated"] = bool(result.get("leadership_brief"))

    # Check required agents were engaged
    findings = result.get("findings", {})
    engaged_agents = list(findings.keys())
    expected_specialist_agents = [a for a in EXPECTED_AGENTS if a != "pm_agent"]
    validations["all_agents_engaged"] = all(
        agent in engaged_agents for agent in expected_specialist_agents
    )

    # Check for findings
    total_findings = sum(
        len(f.get("findings", [])) for f in findings.values()
    )
    validations["findings_generated"] = total_findings > 0

    # Check contradictions were processed
    contradictions = result.get("contradictions", [])
    validations["contradictions_processed"] = isinstance(contradictions, list)

    # Check trace was generated
    validations["trace_generated"] = bool(result.get("trace_id"))

    return validations
