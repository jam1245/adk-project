"""
Earned Value Management (EVM) data for the Advanced Fighter Program (AFP).

Contains current-period EVM metrics, work-package-level performance,
and six months of historical trending data. All values are in USD
and align with the October 2024 reporting period.

Key narrative: WBS 1.3.2 (Wing Assembly) is the primary cost/schedule
variance driver with a CPI of 0.72, caused by supplier quality issues
at Apex Fastener Corp and rework on composite layup tooling.
"""

EVM_METRICS: dict = {
    # --- Headline indices ---
    "CPI": 0.87,
    "SPI": 0.88,
    # --- Dollar variances (cumulative) ---
    "CV": -2_100_000,       # Cost Variance  = BCWP - ACWP
    "SV": -1_800_000,       # Schedule Variance = BCWP - BCWS
    "CV_pct": -12.14,       # CV% = CV / BCWP
    "SV_pct": -10.59,       # SV% = SV / BCWS
    # --- Earned value components (cumulative thru Oct 2024) ---
    "BCWP": 15_200_000,     # Budgeted Cost of Work Performed
    "BCWS": 17_000_000,     # Budgeted Cost of Work Scheduled
    "ACWP": 17_471_264,     # Actual Cost of Work Performed
    # --- At-completion projections ---
    "BAC": 485_000_000,     # Budget at Completion
    "EAC": 557_471_264,     # Estimate at Completion (EAC = BAC / CPI)
    "VAC": -72_471_264,     # Variance at Completion = BAC - EAC
    "EAC_method": "CPI-based (EAC = BAC / CPI)",
    # --- To-complete performance ---
    "TCPI": 1.15,           # To-Complete Performance Index (BAC-based)
    "TCPI_EAC": 1.00,       # TCPI against current EAC
    # --- Period-specific (October 2024 only) ---
    "period_BCWP": 2_450_000,
    "period_BCWS": 2_700_000,
    "period_ACWP": 2_816_092,
    "period_CPI": 0.87,
    "period_SPI": 0.91,
    "reporting_period": "October 2024",
    # --- Work packages (WBS level 3) ---
    "work_packages": [
        {
            "wbs": "1.1",
            "title": "Program Management",
            "BCWP": 2_250_000,
            "BCWS": 2_300_000,
            "ACWP": 2_310_000,
            "CPI": 0.97,
            "SPI": 0.98,
            "BAC": 36_750_000,
            "EAC": 37_886_598,
            "status": "green",
            "variance_explanation": None,
        },
        {
            "wbs": "1.2",
            "title": "Systems Engineering",
            "BCWP": 3_100_000,
            "BCWS": 3_400_000,
            "ACWP": 3_340_000,
            "CPI": 0.93,
            "SPI": 0.91,
            "BAC": 58_200_000,
            "EAC": 62_580_645,
            "status": "yellow",
            "variance_explanation": (
                "Increased integration lab hours for avionics interface "
                "verification; scope growth in cybersecurity requirements "
                "analysis (ref Mod P00027)."
            ),
        },
        {
            "wbs": "1.3.1",
            "title": "Fuselage",
            "BCWP": 2_100_000,
            "BCWS": 2_200_000,
            "ACWP": 2_250_000,
            "CPI": 0.93,
            "SPI": 0.95,
            "BAC": 52_000_000,
            "EAC": 55_913_978,
            "status": "yellow",
            "variance_explanation": (
                "Minor titanium machining rework on frames 4-7; "
                "expected to recover by Q1 FY25."
            ),
        },
        {
            "wbs": "1.3.2",
            "title": "Wing Assembly",
            "BCWP": 1_800_000,
            "BCWS": 2_600_000,
            "ACWP": 2_500_000,
            "CPI": 0.72,
            "SPI": 0.69,
            "BAC": 48_500_000,
            "EAC": 67_361_111,
            "status": "red",
            "variance_explanation": (
                "Primary variance driver. Apex Fastener Corp delivered "
                "fasteners with out-of-spec head geometry (DPMO 8500). "
                "240 units rejected; 12 wing sub-assemblies require "
                "disassembly and rework. Composite layup tooling also "
                "required re-certification after thermal distortion event. "
                "Corrective action CAR-2024-0042 issued."
            ),
        },
        {
            "wbs": "1.3.3",
            "title": "Empennage",
            "BCWP": 1_400_000,
            "BCWS": 1_500_000,
            "ACWP": 1_480_000,
            "CPI": 0.95,
            "SPI": 0.93,
            "BAC": 22_800_000,
            "EAC": 24_000_000,
            "status": "green",
            "variance_explanation": None,
        },
        {
            "wbs": "1.5",
            "title": "Avionics / Mission Systems",
            "BCWP": 2_800_000,
            "BCWS": 3_000_000,
            "ACWP": 3_050_000,
            "CPI": 0.92,
            "SPI": 0.93,
            "BAC": 89_300_000,
            "EAC": 97_065_217,
            "status": "yellow",
            "variance_explanation": (
                "AESA radar firmware integration behind schedule due to "
                "GFE delivery delay from subcontractor; recovery plan in "
                "place targeting December 2024."
            ),
        },
    ],
}

EVM_HISTORY: list[dict] = [
    {
        "period": "May 2024",
        "month": "2024-05",
        "cum_BCWP": 6_500_000,
        "cum_BCWS": 6_800_000,
        "cum_ACWP": 6_900_000,
        "CPI": 0.94,
        "SPI": 0.96,
        "CV": -400_000,
        "SV": -300_000,
        "EAC": 515_957_447,
        "narrative": "Performance nominal; minor SPI softness in SE tasks.",
    },
    {
        "period": "June 2024",
        "month": "2024-06",
        "cum_BCWP": 8_200_000,
        "cum_BCWS": 8_700_000,
        "cum_ACWP": 8_900_000,
        "CPI": 0.92,
        "SPI": 0.94,
        "CV": -700_000,
        "SV": -500_000,
        "EAC": 527_173_913,
        "narrative": (
            "CPI decline driven by unplanned rework on fuselage frames; "
            "Wing Assembly work package beginning to show strain."
        ),
    },
    {
        "period": "July 2024",
        "month": "2024-07",
        "cum_BCWP": 9_800_000,
        "cum_BCWS": 10_600_000,
        "cum_ACWP": 10_880_000,
        "CPI": 0.90,
        "SPI": 0.92,
        "CV": -1_080_000,
        "SV": -800_000,
        "EAC": 538_888_889,
        "narrative": (
            "Apex Fastener Corp first quality escape detected; "
            "initial assessment underway."
        ),
    },
    {
        "period": "August 2024",
        "month": "2024-08",
        "cum_BCWP": 11_300_000,
        "cum_BCWS": 12_500_000,
        "cum_ACWP": 12_640_000,
        "CPI": 0.89,
        "SPI": 0.90,
        "CV": -1_340_000,
        "SV": -1_200_000,
        "EAC": 544_943_820,
        "narrative": (
            "Full scope of fastener defect quantified: 240 units affected. "
            "Wing Assembly CPI drops to 0.76. CAR-2024-0042 issued."
        ),
    },
    {
        "period": "September 2024",
        "month": "2024-09",
        "cum_BCWP": 13_100_000,
        "cum_BCWS": 14_600_000,
        "cum_ACWP": 14_942_529,
        "CPI": 0.88,
        "SPI": 0.90,
        "CV": -1_842_529,
        "SV": -1_500_000,
        "EAC": 551_136_364,
        "narrative": (
            "Wing sub-assembly rework in progress; schedule impact "
            "crystallizing at 30+ day slip to Wing Assembly Complete "
            "milestone."
        ),
    },
    {
        "period": "October 2024",
        "month": "2024-10",
        "cum_BCWP": 15_200_000,
        "cum_BCWS": 17_000_000,
        "cum_ACWP": 17_471_264,
        "CPI": 0.87,
        "SPI": 0.88,
        "CV": -2_100_000,
        "SV": -1_800_000,
        "EAC": 557_471_264,
        "narrative": (
            "Continued CPI/SPI erosion. Wing Assembly CPI at 0.72. "
            "TCPI now 1.15 indicating significant recovery challenge. "
            "Program office evaluating management reserve release and "
            "potential re-baseline."
        ),
    },
]
