"""
Scenario 3: Supplier Quality Escape Causing Rework and Risk Escalation

This scenario demonstrates the workbench handling a quality escape
notification requiring containment, investigation, and recovery planning.

Setup:
- Program: Advanced Fighter Program (AFP)
- Event: Customer discovered defective wing fasteners during acceptance inspection
- Quantity: 240 fasteners across 12 wing assemblies
- Impact: Stop-ship issued, 100% re-inspection required, potential rework
- Trigger: Quality escape notification from customer
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone

# Scenario configuration
SCENARIO_NAME = "supplier_quality_escape"
SCENARIO_TITLE = "Supplier Quality Escape Causing Rework and Risk Escalation"

SCENARIO_TRIGGER = """
QUALITY ESCAPE NOTIFICATION - IMMEDIATE ACTION REQUIRED

Program: Advanced Fighter Program (AFP)
Contract: FA8611-21-C-0042
Date: October 18, 2024

CUSTOMER NOTIFICATION:
During acceptance inspection at the Government facility, defective wing
fasteners were discovered. A stop-ship has been issued pending resolution.

ESCAPE DETAILS:
- Part Number: AFP-WF-Ti-001 (Ti-6Al-4V Wing Fastener)
- Supplier: Apex Fastener Corp
- Defect: Insufficient torque retention - fasteners backing out under vibration
- Quantity Affected: 240 fasteners
- Assemblies Affected: 12 wing assemblies (S/N WA-024 through WA-035)
- Discovery Method: Customer acceptance inspection
- Severity: Critical (potential flight safety issue)

IMMEDIATE ACTIONS TAKEN:
1. Stop-ship issued for all wing assemblies in queue
2. Affected assemblies quarantined
3. Supplier notified and shipments suspended

REQUEST: Conduct full quality escape investigation including:
1. Containment verification and scope confirmation
2. Root cause analysis with 8D documentation
3. Cost of Poor Quality (COPQ) calculation
4. Schedule impact assessment
5. Customer notification requirements
6. Corrective and preventive action plan
7. Supplier risk escalation assessment
"""

EXPECTED_AGENTS = [
    "sq_agent",         # Quality escape investigation, containment
    "rca_agent",        # Root cause analysis (8D)
    "cam_agent",        # COPQ and schedule impact
    "contracts_agent",  # Customer notification, warranty
    "risk_agent",       # Supplier risk escalation
    "pm_agent",         # Executive communication, recovery plan
]

EXPECTED_OUTPUTS = {
    "leadership_brief": {
        "format": "markdown",
        "sections": ["WHAT HAPPENED", "WHY IT HAPPENED", "SO WHAT", "NOW WHAT"],
        "risk_level": "high",
    },
    "eight_d_report": {
        "problem": "Defective wing fasteners - insufficient torque retention",
        "containment": "Stop-ship, quarantine, 100% sort",
        "root_cause": "Supplier torque process not validated",
        "corrective_action": "Process revalidation, 100% testing",
        "preventive_action": "Supplier audit, dual-source qualification",
    },
    "cam_narrative": {
        "copq_total": 180000,
        "schedule_impact_weeks": 3,
        "components": ["rework_labor", "replacement_material", "inspection", "delay"],
    },
    "risk_register_updates": {
        "risk_id": "R-001",
        "new_probability": 0.85,
        "new_impact": "Major",
        "status": "escalated",
    },
    "action_items": {
        "categories": [
            "containment",
            "root_cause",
            "corrective_action",
            "customer_notification",
            "supplier_management",
        ],
    },
}


def get_scenario_context() -> dict:
    """Get the context data for this scenario.

    Returns
    -------
    dict
        Context including quality escape details and supplier data.
    """
    return {
        "program_name": "Advanced Fighter Program (AFP)",
        "reporting_period": "October 2024",
        "quality_escape": {
            "escape_id": "QE-2024-003",
            "severity": "critical",
            "discovery_date": "2024-10-18",
            "supplier": "Apex Fastener Corp",
            "part_number": "AFP-WF-Ti-001",
            "part_description": "Ti-6Al-4V Wing Fastener",
            "defect_description": (
                "Insufficient torque retention - fasteners backing out "
                "under vibration testing"
            ),
            "units_affected": 240,
            "assemblies_affected": 12,
            "assembly_serial_range": "WA-024 through WA-035",
            "discovery_method": "Customer acceptance inspection",
            "containment_status": "Stop-ship issued, assemblies quarantined",
        },
        "supplier_metrics": {
            "supplier_name": "Apex Fastener Corp",
            "otdp_percent": 72,
            "dpmo": 8500,
            "quality_rating": 2.2,
            "status": "probationary",
            "open_cars": 3,
        },
        "cost_impact_estimate": {
            "rework_labor": 85_000,
            "replacement_material": 42_000,
            "inspection": 28_000,
            "engineering_disposition": 15_000,
            "schedule_delay": 10_000,
            "total": 180_000,
        },
        "schedule_impact": {
            "delay_weeks": 3,
            "affected_milestones": [
                "Wing Assembly Complete",
                "Final Assembly Rollout",
                "First Flight",
            ],
        },
    }


async def run_scenario(orchestrator) -> dict:
    """Execute the quality escape scenario.

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
    print(f"SCENARIO 3: {SCENARIO_TITLE}")
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
    print("SCENARIO 3 COMPLETE")
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

    # Check case file has correct intent
    case_file = result.get("case_file", {})
    validations["correct_intent"] = (
        case_file.get("intent") == "supplier_quality_investigation"
    )

    # Check trace was generated
    validations["trace_generated"] = bool(result.get("trace_id"))

    # Verify SQ agent was definitely included (critical for this scenario)
    validations["sq_agent_engaged"] = "sq_agent" in engaged_agents

    return validations
