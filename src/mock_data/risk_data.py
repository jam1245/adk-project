"""
Risk register for the Advanced Fighter Program (AFP).

Contains the program risk register with probability, impact, risk scores,
mitigation plans, and ownership. Risk scores use a 5x5 matrix
(probability 1-5 x impact 1-5, score 1-25).

Aligned with the October 2024 reporting period.
"""

RISK_REGISTER: list[dict] = [
    {
        "risk_id": "R-001",
        "title": "Supplier Fastener Quality Deficiency",
        "category": "supply_chain",
        "description": (
            "Apex Fastener Corp has delivered wing fasteners with "
            "out-of-specification head geometry (DPMO 8500). 240 units "
            "have been rejected, requiring disassembly and rework of "
            "12 wing sub-assemblies. Root cause traced to worn tooling "
            "at supplier's Tier 2 forging source."
        ),
        "probability": 0.95,
        "probability_score": 5,
        "impact": "critical",
        "impact_score": 5,
        "risk_score": 25,
        "risk_level": "critical",
        "status": "active",
        "date_identified": "2024-07-18",
        "last_updated": "2024-10-28",
        "owner": "David Moreno, Contractor PM",
        "mitigation": (
            "CAR-2024-0042 issued to Apex Fastener Corp. Mandatory source "
            "inspection implemented. Alternate supplier (Titan Precision "
            "Fasteners) qualified as second source. Replacement lot on "
            "order with delivery expected 2024-12-06."
        ),
        "contingency": (
            "If replacement fasteners fail re-inspection, program will "
            "invoke MR draw-down (est. $1.8M) and engage Titan Precision "
            "Fasteners for emergency production run."
        ),
        "affected_milestones": ["MS-006", "MS-009", "MS-010"],
        "cost_impact_estimate": 3_200_000,
        "schedule_impact_days": 30,
    },
    {
        "risk_id": "R-002",
        "title": "Wing Assembly Schedule Overrun",
        "category": "schedule",
        "description": (
            "Wing Assembly Complete milestone (MS-006) is forecasting a "
            "30-day slip due to cascading effects of fastener rework and "
            "composite tooling re-certification. Critical path directly "
            "affected."
        ),
        "probability": 0.90,
        "probability_score": 5,
        "impact": "high",
        "impact_score": 4,
        "risk_score": 20,
        "risk_level": "high",
        "status": "active",
        "date_identified": "2024-08-05",
        "last_updated": "2024-10-28",
        "owner": "Dr. Alan Whitfield, Chief Engineer",
        "mitigation": (
            "Authorized 2nd shift operations for wing assembly line. "
            "Parallel processing of sub-assemblies 7-12 where feasible. "
            "Weekly recovery schedule reviews with IPT leads."
        ),
        "contingency": (
            "Request schedule re-baseline through formal EAC process if "
            "30-day recovery is not achievable by January 2025."
        ),
        "affected_milestones": ["MS-006", "MS-009", "MS-010"],
        "cost_impact_estimate": 1_800_000,
        "schedule_impact_days": 30,
    },
    {
        "risk_id": "R-003",
        "title": "AESA Radar Firmware Integration Delay",
        "category": "technical",
        "description": (
            "Government-Furnished Equipment (GFE) AESA radar firmware "
            "v2.4 delivery from subcontractor delayed by 14 days. "
            "Integration lab testing cannot proceed until delivery, "
            "potentially impacting AIL Readiness milestone."
        ),
        "probability": 0.60,
        "probability_score": 3,
        "impact": "high",
        "impact_score": 4,
        "risk_score": 12,
        "risk_level": "medium",
        "status": "active",
        "date_identified": "2024-09-12",
        "last_updated": "2024-10-25",
        "owner": "Lt Col. James Park, Deputy PM",
        "mitigation": (
            "Coordinating with GFE program office for expedited delivery. "
            "Integration lab pre-staging with emulator to maximize "
            "productive time once firmware arrives. Bi-weekly sync with "
            "radar subcontractor."
        ),
        "contingency": (
            "If firmware delivery slips beyond November 2024, request "
            "GFE program office intervention and evaluate simulator-based "
            "partial integration credit."
        ),
        "affected_milestones": ["MS-008"],
        "cost_impact_estimate": 750_000,
        "schedule_impact_days": 16,
    },
    {
        "risk_id": "R-004",
        "title": "Cybersecurity Requirements Scope Growth",
        "category": "requirements",
        "description": (
            "Contract Mod P00027 added cybersecurity CDRL requirements "
            "that were not in the original baseline. Systems Engineering "
            "effort has increased to support RMF documentation and "
            "penetration testing coordination. Full impact still being "
            "assessed."
        ),
        "probability": 0.70,
        "probability_score": 4,
        "impact": "medium",
        "impact_score": 3,
        "risk_score": 12,
        "risk_level": "medium",
        "status": "active",
        "date_identified": "2024-06-20",
        "last_updated": "2024-10-15",
        "owner": "Kevin Tran, EVM Analyst",
        "mitigation": (
            "Mod P00027 provides $450K additional funding and 8-week "
            "schedule extension for cybersecurity scope. Dedicated cyber "
            "SME added to SE team. CDRL A012 (Cybersecurity Assessment "
            "Report) baselined."
        ),
        "contingency": (
            "If RMF documentation effort exceeds mod funding, submit "
            "REA for additional scope/cost adjustment."
        ),
        "affected_milestones": [],
        "cost_impact_estimate": 450_000,
        "schedule_impact_days": 0,
    },
    {
        "risk_id": "R-005",
        "title": "Composite Material Shelf-Life Expiration",
        "category": "supply_chain",
        "description": (
            "Pre-preg composite material (IM7/5320-1) for wing skin "
            "panels approaching shelf-life limit. Schedule delays may "
            "cause material to expire before layup, requiring new "
            "procurement with 16-week lead time."
        ),
        "probability": 0.40,
        "probability_score": 2,
        "impact": "high",
        "impact_score": 4,
        "risk_score": 8,
        "risk_level": "medium",
        "status": "watch",
        "date_identified": "2024-10-01",
        "last_updated": "2024-10-28",
        "owner": "Dr. Alan Whitfield, Chief Engineer",
        "mitigation": (
            "Material coupon testing scheduled for November 2024 to "
            "validate remaining usable life. Contingency order placed "
            "with Hexcel for replacement material (PO MAS-2024-1187)."
        ),
        "contingency": (
            "If coupon testing fails, invoke contingency PO and accept "
            "16-week procurement delay. Evaluate impact to MS-006 "
            "recovery plan."
        ),
        "affected_milestones": ["MS-006"],
        "cost_impact_estimate": 620_000,
        "schedule_impact_days": 112,
    },
    {
        "risk_id": "R-006",
        "title": "Propulsion Integration Thermal Margin",
        "category": "technical",
        "description": (
            "Thermal analysis indicates engine bay temperatures may "
            "exceed design margins by 15-20 degrees F during sustained "
            "supersonic cruise. Could require redesign of thermal "
            "protection blankets and associated structural brackets."
        ),
        "probability": 0.35,
        "probability_score": 2,
        "impact": "high",
        "impact_score": 4,
        "risk_score": 8,
        "risk_level": "medium",
        "status": "watch",
        "date_identified": "2024-08-22",
        "last_updated": "2024-10-20",
        "owner": "Dr. Alan Whitfield, Chief Engineer",
        "mitigation": (
            "Instrumented ground test (MS-007) will provide empirical "
            "thermal data. CFD model being refined with updated boundary "
            "conditions. Design contingency for upgraded blankets "
            "identified (Nextel 720 option)."
        ),
        "contingency": (
            "If ground test confirms exceedance, implement Nextel 720 "
            "thermal blanket redesign. Estimated cost $1.2M, 45-day "
            "schedule impact to Final Assembly."
        ),
        "affected_milestones": ["MS-007", "MS-009"],
        "cost_impact_estimate": 1_200_000,
        "schedule_impact_days": 45,
    },
    {
        "risk_id": "R-007",
        "title": "Flight Test Range Availability",
        "category": "external",
        "description": (
            "Edwards AFB flight test range scheduling conflict with "
            "another program may limit available test windows for First "
            "Flight and initial flight envelope expansion. Range "
            "allocation not confirmed beyond March 2026."
        ),
        "probability": 0.30,
        "probability_score": 2,
        "impact": "medium",
        "impact_score": 3,
        "risk_score": 6,
        "risk_level": "low",
        "status": "watch",
        "date_identified": "2024-05-10",
        "last_updated": "2024-10-05",
        "owner": "Col. Rebecca Torres, Government PM",
        "mitigation": (
            "Formal range request submitted to 412th Test Wing for "
            "Q1-Q2 2026 windows. Backup request submitted to NAS Patuxent "
            "River. Pre-coordination meetings scheduled for January 2025."
        ),
        "contingency": (
            "If Edwards AFB unavailable, execute First Flight from NAS "
            "Patuxent River with temporary test infrastructure. Additional "
            "cost estimate: $800K."
        ),
        "affected_milestones": ["MS-010"],
        "cost_impact_estimate": 800_000,
        "schedule_impact_days": 21,
    },
    {
        "risk_id": "R-008",
        "title": "Software Lab Integration Environment Stability",
        "category": "technical",
        "description": (
            "Software integration lab environment experiencing "
            "intermittent network latency issues affecting HIL "
            "(Hardware-in-the-Loop) test execution reliability. "
            "Approximately 8% of test runs require re-execution."
        ),
        "probability": 0.50,
        "probability_score": 3,
        "impact": "low",
        "impact_score": 2,
        "risk_score": 6,
        "risk_level": "low",
        "status": "active",
        "date_identified": "2024-09-05",
        "last_updated": "2024-10-22",
        "owner": "David Moreno, Contractor PM",
        "mitigation": (
            "Network infrastructure upgrade planned for November 2024. "
            "Temporary mitigation: increased test execution buffer in "
            "schedule (10% margin added to software test tasks)."
        ),
        "contingency": (
            "If network upgrade does not resolve, procure dedicated "
            "test network segment. Estimated cost: $180K."
        ),
        "affected_milestones": [],
        "cost_impact_estimate": 180_000,
        "schedule_impact_days": 0,
    },
]

RISK_SUMMARY: dict = {
    "total_risks": 8,
    "critical": 1,
    "high": 1,
    "medium": 3,
    "low": 3,
    "active": 5,
    "watch": 3,
    "closed": 0,
    "top_risk": "R-001",
    "total_cost_exposure": 9_000_000,
    "reporting_period": "October 2024",
}
