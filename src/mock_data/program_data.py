"""
Program-level snapshot data for the Advanced Fighter Program (AFP).

Provides top-level program metadata, key personnel, budget summary,
and WBS structure used across all demo scenarios.
"""

PROGRAM_SNAPSHOT: dict = {
    "program_name": "Advanced Fighter Program (AFP)",
    "contract_number": "FA8611-21-C-0042",
    "prime_contractor": "Meridian Aerospace Systems",
    "contracting_agency": "AFLCMC/WIZ, Wright-Patterson AFB, OH",
    "contract_type": "CPIF",
    "program_phase": "EMD",
    "reporting_period": "October 2024",
    "reporting_period_start": "2024-10-01",
    "reporting_period_end": "2024-10-31",
    "program_start_date": "2021-09-15",
    "planned_completion_date": "2027-06-30",
    "total_budget": 485_000_000,
    "budget_at_completion": 485_000_000,
    "management_reserve": 12_000_000,
    "undistributed_budget": 3_200_000,
    "currency": "USD",
    "security_classification": "UNCLASSIFIED // FOR DEMONSTRATION ONLY",
    "key_personnel": {
        "program_manager": {
            "name": "Col. Rebecca Torres",
            "organization": "AFLCMC/WIZ",
            "role": "Government Program Manager",
            "phone": "(937) 255-3841",
        },
        "deputy_program_manager": {
            "name": "Lt Col. James Park",
            "organization": "AFLCMC/WIZ",
            "role": "Deputy Program Manager",
            "phone": "(937) 255-3842",
        },
        "chief_engineer": {
            "name": "Dr. Alan Whitfield",
            "organization": "Meridian Aerospace Systems",
            "role": "Chief Engineer",
            "phone": "(817) 555-0147",
        },
        "contracts_officer": {
            "name": "Maria Santos",
            "organization": "AFLCMC/PKA",
            "role": "Procuring Contracting Officer (PCO)",
            "phone": "(937) 255-3900",
        },
        "evms_analyst": {
            "name": "Kevin Tran",
            "organization": "AFLCMC/WIZ",
            "role": "EVM Analyst / IPMR Lead",
            "phone": "(937) 255-3850",
        },
        "contractor_pm": {
            "name": "David Moreno",
            "organization": "Meridian Aerospace Systems",
            "role": "Contractor Program Manager",
            "phone": "(817) 555-0100",
        },
    },
    "wbs_summary": [
        {
            "wbs": "1.0",
            "title": "Advanced Fighter Program",
            "budget": 485_000_000,
            "level": 1,
        },
        {
            "wbs": "1.1",
            "title": "Program Management",
            "budget": 36_750_000,
            "level": 2,
        },
        {
            "wbs": "1.2",
            "title": "Systems Engineering",
            "budget": 58_200_000,
            "level": 2,
        },
        {
            "wbs": "1.3",
            "title": "Airframe",
            "budget": 142_000_000,
            "level": 2,
        },
        {
            "wbs": "1.3.1",
            "title": "Fuselage",
            "budget": 52_000_000,
            "level": 3,
        },
        {
            "wbs": "1.3.2",
            "title": "Wing Assembly",
            "budget": 48_500_000,
            "level": 3,
        },
        {
            "wbs": "1.3.3",
            "title": "Empennage",
            "budget": 22_800_000,
            "level": 3,
        },
        {
            "wbs": "1.3.4",
            "title": "Canopy & Crew Station",
            "budget": 18_700_000,
            "level": 3,
        },
        {
            "wbs": "1.4",
            "title": "Propulsion Integration",
            "budget": 67_500_000,
            "level": 2,
        },
        {
            "wbs": "1.5",
            "title": "Avionics / Mission Systems",
            "budget": 89_300_000,
            "level": 2,
        },
        {
            "wbs": "1.6",
            "title": "Software",
            "budget": 42_100_000,
            "level": 2,
        },
        {
            "wbs": "1.7",
            "title": "Test & Evaluation",
            "budget": 31_500_000,
            "level": 2,
        },
        {
            "wbs": "1.8",
            "title": "Training Systems",
            "budget": 8_650_000,
            "level": 2,
        },
        {
            "wbs": "1.9",
            "title": "Data & Documentation",
            "budget": 9_000_000,
            "level": 2,
        },
    ],
}
