"""
Scenario 2: Assess Contract Change Mod Impacting Deliverables

This scenario demonstrates the workbench handling a contract modification
assessment request for a new cybersecurity CDRL requirement.

Setup:
- Program: Advanced Fighter Program (AFP)
- Contract Mod: P00027 - Adds Cybersecurity CDRL (deliverable)
- Mod Type: Bilateral, negotiated change
- Trigger: Mod received, requires impact assessment
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone

# Scenario configuration
SCENARIO_NAME = "contract_change_assessment"
SCENARIO_TITLE = "Assess Contract Change Mod Impacting Deliverables"

SCENARIO_TRIGGER = """
CONTRACT MODIFICATION RECEIVED - Requires Impact Assessment

Program: Advanced Fighter Program (AFP)
Contract: FA8611-21-C-0042

MODIFICATION DETAILS:
- Mod Number: P00027
- Mod Type: Bilateral (Negotiated Change)
- Effective Date: 2024-10-15

SCOPE OF CHANGE:
The Government is adding a new Contract Data Requirements List (CDRL) item:
- CDRL A012: Cybersecurity Assessment Report
- DID: DI-MISC-81466
- Frequency: Quarterly, with final delivery at CDR+90 days
- Classification: CUI
- Distribution: Statement D (DoD and U.S. DoD Contractors Only)

GOVERNMENT POSITION:
- Proposed cost increase: $450,000
- Proposed schedule extension: 8 weeks for initial development

REQUEST: Assess the full impact of this modification including:
1. Cost impact analysis (direct, indirect, fee)
2. Schedule impact on program milestones
3. Resource requirements
4. Risk implications
5. Recommendation (accept/negotiate/reject)
"""

EXPECTED_AGENTS = [
    "contracts_agent",  # Contract interpretation, obligations
    "cam_agent",        # Cost and schedule impact
    "risk_agent",       # New risk identification
    "pm_agent",         # Impact assessment synthesis
]

EXPECTED_OUTPUTS = {
    "leadership_brief": {
        "format": "markdown",
        "sections": ["WHAT HAPPENED", "WHY IT HAPPENED", "SO WHAT", "NOW WHAT"],
    },
    "contract_change_summary": {
        "mod_number": "P00027",
        "cost_impact": 450000,
        "schedule_impact_weeks": 8,
        "new_deliverables": ["CDRL A012 - Cybersecurity Assessment Report"],
    },
    "risk_register_updates": {
        "new_risk": "Cybersecurity certification authority delays",
        "probability": 0.65,
        "impact": "Major",
    },
    "baseline_change_proposal": {
        "cost_delta": 450000,
        "schedule_delta_weeks": 8,
    },
}


def get_scenario_context() -> dict:
    """Get the context data for this scenario.

    Returns
    -------
    dict
        Context including contract mod details and current baseline.
    """
    return {
        "program_name": "Advanced Fighter Program (AFP)",
        "reporting_period": "October 2024",
        "contract_mod": {
            "mod_number": "P00027",
            "mod_type": "bilateral",
            "title": "Add Cybersecurity Assessment Report CDRL",
            "description": (
                "Government-directed addition of quarterly cybersecurity "
                "assessment reporting per DI-MISC-81466"
            ),
            "proposed_cost_impact": 450_000,
            "proposed_schedule_impact_weeks": 8,
            "new_deliverables": [
                {
                    "cdrl_id": "A012",
                    "title": "Cybersecurity Assessment Report",
                    "did": "DI-MISC-81466",
                    "frequency": "Quarterly",
                    "classification": "CUI",
                }
            ],
        },
        "current_baseline": {
            "contract_value": 485_000_000,
            "period_of_performance_end": "2027-09-30",
            "cdrl_count": 11,
        },
    }


async def run_scenario(orchestrator) -> dict:
    """Execute the contract change assessment scenario.

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
    print(f"SCENARIO 2: {SCENARIO_TITLE}")
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
    print("SCENARIO 2 COMPLETE")
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
        case_file.get("intent") == "assess_contract_change"
    )

    # Check trace was generated
    validations["trace_generated"] = bool(result.get("trace_id"))

    return validations
