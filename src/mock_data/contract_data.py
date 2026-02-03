"""
Contract data for the Advanced Fighter Program (AFP).

Contains the contract baseline, modification history, and Contract Data
Requirements List (CDRL). Aligned with the October 2024 reporting period.

Key narrative: Mod P00027 added cybersecurity CDRL requirements (+$450K,
+8 weeks), reflecting evolving DoD cybersecurity mandates.
"""

CONTRACT_BASELINE: dict = {
    "contract_number": "FA8611-21-C-0042",
    "contract_type": "CPIF",
    "prime_contractor": "Meridian Aerospace Systems",
    "contractor_duns": "078541236",
    "contractor_cage": "3A7B2",
    "contracting_office": "AFLCMC/PKA",
    "administering_office": "DCMA Dallas",
    "award_date": "2021-09-15",
    "period_of_performance_start": "2021-09-15",
    "period_of_performance_end": "2027-06-30",
    "original_contract_value": 478_000_000,
    "current_contract_value": 485_000_000,
    "funded_to_date": 312_000_000,
    "unfunded_balance": 173_000_000,
    "fee_structure": {
        "target_cost": 470_000_000,
        "target_fee": 37_600_000,
        "target_fee_pct": 8.0,
        "minimum_fee_pct": 3.0,
        "maximum_fee_pct": 12.0,
        "share_ratio_over": "80/20",
        "share_ratio_under": "70/30",
        "ceiling_price": 564_000_000,
    },
    "clin_summary": [
        {
            "clin": "0001",
            "description": "EMD - Air Vehicle (CPIF)",
            "funded_amount": 245_000_000,
            "ceiling": 420_000_000,
        },
        {
            "clin": "0002",
            "description": "EMD - Systems Engineering & Program Management (CPIF)",
            "funded_amount": 52_000_000,
            "ceiling": 94_950_000,
        },
        {
            "clin": "0003",
            "description": "Test & Evaluation Support (CPIF)",
            "funded_amount": 11_000_000,
            "ceiling": 31_500_000,
        },
        {
            "clin": "0004",
            "description": "Data & Documentation (FFP)",
            "funded_amount": 4_000_000,
            "ceiling": 9_000_000,
        },
    ],
    "evms_applicable": True,
    "evms_system": "Meridian Aerospace EVM System (DCMA validated 2022-04-12)",
    "security_classification": "UNCLASSIFIED // FOR DEMONSTRATION ONLY",
}

CONTRACT_MODS: list[dict] = [
    {
        "mod_number": "P00001",
        "title": "Administrative Correction - DPAS Rating",
        "mod_type": "administrative",
        "effective_date": "2021-11-02",
        "description": (
            "Corrected DPAS rating from DO-A3 to DX-A3 per OUSD(A&S) "
            "directive. No cost or schedule impact."
        ),
        "cost_impact": 0,
        "schedule_impact_weeks": 0,
        "new_contract_value": 478_000_000,
        "status": "executed",
        "contracting_officer": "Maria Santos",
    },
    {
        "mod_number": "P00014",
        "title": "GFE Radar Integration Support",
        "mod_type": "bilateral",
        "effective_date": "2023-08-18",
        "description": (
            "Added scope for AESA radar GFE integration support, "
            "including interface control document development, integration "
            "lab modifications, and firmware compatibility testing. "
            "Negotiated definitization of previously undefinitized "
            "change order UCO-2023-003."
        ),
        "cost_impact": 3_850_000,
        "schedule_impact_weeks": 0,
        "new_contract_value": 481_850_000,
        "status": "executed",
        "contracting_officer": "Maria Santos",
        "clins_affected": ["0001", "0002"],
        "funding_added": 3_850_000,
    },
    {
        "mod_number": "P00022",
        "title": "Engineering Change Proposal - Canopy De-Icing System",
        "mod_type": "bilateral",
        "effective_date": "2024-03-01",
        "description": (
            "Incorporated ECP-2024-008 for upgraded canopy de-icing "
            "system to meet revised environmental envelope requirements "
            "(-65F to +160F). Includes redesign of heating element "
            "routing, updated wiring harness, and qualification testing."
        ),
        "cost_impact": 2_700_000,
        "schedule_impact_weeks": 4,
        "new_contract_value": 484_550_000,
        "status": "executed",
        "contracting_officer": "Maria Santos",
        "clins_affected": ["0001"],
        "funding_added": 2_700_000,
    },
    {
        "mod_number": "P00027",
        "title": "Cybersecurity CDRL Addition - RMF Assessment",
        "mod_type": "bilateral",
        "effective_date": "2024-06-15",
        "description": (
            "Added cybersecurity assessment requirements per "
            "DoDI 8510.01 (Risk Management Framework). New CDRL A012 "
            "(Cybersecurity Assessment Report) established. Scope "
            "includes security control assessment, penetration testing "
            "coordination, and Authority to Operate (ATO) documentation "
            "support. Addresses findings from OUSD(R&E) cybersecurity "
            "review of tactical aircraft programs."
        ),
        "cost_impact": 450_000,
        "schedule_impact_weeks": 8,
        "new_contract_value": 485_000_000,
        "status": "executed",
        "contracting_officer": "Maria Santos",
        "clins_affected": ["0002", "0004"],
        "funding_added": 450_000,
        "new_period_of_performance_end": None,
        "cdrl_added": "A012",
    },
]

CDRL_LIST: list[dict] = [
    {
        "cdrl_id": "A001",
        "did_number": "DI-MGMT-81466B",
        "title": "Contractor's Progress, Status, and Management Report",
        "frequency": "Monthly",
        "distribution": "Government PM, DCMA",
        "classification": "UNCLASSIFIED",
        "status": "current",
        "last_submission": "2024-10-31",
        "next_due": "2024-11-30",
        "notes": None,
    },
    {
        "cdrl_id": "A002",
        "did_number": "DI-MGMT-81861",
        "title": "Integrated Program Management Report (IPMR)",
        "frequency": "Monthly",
        "distribution": "Government PM, DCMA, EVM Analyst",
        "classification": "UNCLASSIFIED",
        "status": "current",
        "last_submission": "2024-10-31",
        "next_due": "2024-11-30",
        "notes": "Formats 1-7. EVMS validated April 2022.",
    },
    {
        "cdrl_id": "A003",
        "did_number": "DI-SESS-81521C",
        "title": "System/Subsystem Specification",
        "frequency": "Event-driven",
        "distribution": "Government PM, Chief Engineer",
        "classification": "UNCLASSIFIED",
        "status": "current",
        "last_submission": "2024-06-18",
        "next_due": None,
        "notes": "Updated at CDR. Next update at TRR.",
    },
    {
        "cdrl_id": "A004",
        "did_number": "DI-NDTI-80809B",
        "title": "Test Plan / Test Procedures",
        "frequency": "Event-driven",
        "distribution": "Government PM, T&E Lead",
        "classification": "UNCLASSIFIED",
        "status": "current",
        "last_submission": "2024-09-15",
        "next_due": "2025-01-15",
        "notes": "Flight test plan due 90 days prior to First Flight.",
    },
    {
        "cdrl_id": "A005",
        "did_number": "DI-QCIC-80553A",
        "title": "Inspection and Test Report",
        "frequency": "Event-driven",
        "distribution": "DCMA QAR, Government PM",
        "classification": "UNCLASSIFIED",
        "status": "current",
        "last_submission": "2024-10-12",
        "next_due": None,
        "notes": "Includes NDI results for composite structures.",
    },
    {
        "cdrl_id": "A006",
        "did_number": "DI-MGMT-81334C",
        "title": "Integrated Master Schedule (IMS)",
        "frequency": "Monthly",
        "distribution": "Government PM, DCMA",
        "classification": "UNCLASSIFIED",
        "status": "current",
        "last_submission": "2024-10-31",
        "next_due": "2024-11-30",
        "notes": "MS Project XML format per DID requirements.",
    },
    {
        "cdrl_id": "A007",
        "did_number": "DI-ILSS-81495C",
        "title": "Technical Manual - Organizational Maintenance",
        "frequency": "Event-driven",
        "distribution": "Government PM, Logistics Lead",
        "classification": "UNCLASSIFIED",
        "status": "in_development",
        "last_submission": None,
        "next_due": "2026-01-15",
        "notes": "Preliminary draft due 18 months prior to IOC.",
    },
    {
        "cdrl_id": "A008",
        "did_number": "DI-MGMT-81650",
        "title": "Risk Management Report",
        "frequency": "Monthly",
        "distribution": "Government PM, Deputy PM",
        "classification": "UNCLASSIFIED",
        "status": "current",
        "last_submission": "2024-10-31",
        "next_due": "2024-11-30",
        "notes": None,
    },
    {
        "cdrl_id": "A009",
        "did_number": "DI-SESS-81748",
        "title": "Software Development Plan",
        "frequency": "Event-driven",
        "distribution": "Government PM, Chief Engineer",
        "classification": "UNCLASSIFIED",
        "status": "current",
        "last_submission": "2024-02-28",
        "next_due": None,
        "notes": "Approved version 3.1. Agile methodology per DevSecOps guidance.",
    },
    {
        "cdrl_id": "A010",
        "did_number": "DI-ENVR-80198C",
        "title": "Environmental Compliance Report",
        "frequency": "Annually",
        "distribution": "Government PM, Environmental Office",
        "classification": "UNCLASSIFIED",
        "status": "current",
        "last_submission": "2024-09-30",
        "next_due": "2025-09-30",
        "notes": "NEPA compliance documentation.",
    },
    {
        "cdrl_id": "A011",
        "did_number": "DI-MISC-81508",
        "title": "Contractor's Configuration Management Plan",
        "frequency": "Event-driven",
        "distribution": "Government PM, DCMA",
        "classification": "UNCLASSIFIED",
        "status": "current",
        "last_submission": "2023-06-01",
        "next_due": None,
        "notes": "Approved version 2.0.",
    },
    {
        "cdrl_id": "A012",
        "did_number": "DI-MGMT-82187",
        "title": "Cybersecurity Assessment Report",
        "frequency": "Event-driven",
        "distribution": "Government PM, ISSM, AO",
        "classification": "CUI",
        "status": "in_development",
        "last_submission": None,
        "next_due": "2025-02-15",
        "notes": (
            "Added via Mod P00027. Covers RMF security control assessment, "
            "penetration test results, and ATO package documentation."
        ),
    },
]
