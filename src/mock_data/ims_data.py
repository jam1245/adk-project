"""
Integrated Master Schedule (IMS) milestone data for the Advanced Fighter
Program (AFP).

Contains the top-level milestone list, critical-path analysis, and
schedule health indicators aligned with the October 2024 reporting period.

Key narrative: The "Wing Assembly Complete" milestone (MS-006) has slipped
30 days due to supplier quality issues at Apex Fastener Corp, placing
downstream milestones at risk.
"""

IMS_MILESTONES: list[dict] = [
    {
        "milestone_id": "MS-001",
        "title": "System Requirements Review (SRR)",
        "wbs": "1.2",
        "baseline_date": "2022-03-15",
        "forecast_date": "2022-03-15",
        "actual_date": "2022-03-15",
        "slip_days": 0,
        "status": "completed",
        "is_key_event": True,
        "notes": "Completed on schedule. All entrance/exit criteria met.",
    },
    {
        "milestone_id": "MS-002",
        "title": "Preliminary Design Review (PDR)",
        "wbs": "1.2",
        "baseline_date": "2023-01-20",
        "forecast_date": "2023-01-20",
        "actual_date": "2023-01-27",
        "slip_days": 7,
        "status": "completed",
        "is_key_event": True,
        "notes": (
            "Completed 7 days late due to open RIDs on thermal management "
            "design. All RIDs resolved by February 2023."
        ),
    },
    {
        "milestone_id": "MS-003",
        "title": "Critical Design Review (CDR)",
        "wbs": "1.2",
        "baseline_date": "2024-06-15",
        "forecast_date": "2024-06-15",
        "actual_date": "2024-06-18",
        "slip_days": 3,
        "status": "completed",
        "is_key_event": True,
        "notes": (
            "Completed 3 days late. Three Category 1 RIDs remain open "
            "(RID-CDR-017, -023, -041); resolution tracked weekly."
        ),
    },
    {
        "milestone_id": "MS-004",
        "title": "Fuselage Major Assembly Start",
        "wbs": "1.3.1",
        "baseline_date": "2024-08-01",
        "forecast_date": "2024-08-01",
        "actual_date": "2024-08-05",
        "slip_days": 4,
        "status": "completed",
        "is_key_event": False,
        "notes": "Minor delay for tooling calibration; no downstream impact.",
    },
    {
        "milestone_id": "MS-005",
        "title": "Wing Skin Panel Layup Complete",
        "wbs": "1.3.2",
        "baseline_date": "2024-09-30",
        "forecast_date": "2024-09-30",
        "actual_date": "2024-10-12",
        "slip_days": 12,
        "status": "completed",
        "is_key_event": False,
        "notes": (
            "Delayed by composite layup tooling re-certification after "
            "thermal distortion event. Skin panels passed NDI inspection "
            "on second attempt."
        ),
    },
    {
        "milestone_id": "MS-006",
        "title": "Wing Assembly Complete",
        "wbs": "1.3.2",
        "baseline_date": "2025-01-15",
        "forecast_date": "2025-02-14",
        "actual_date": None,
        "slip_days": 30,
        "status": "slipped",
        "is_key_event": True,
        "notes": (
            "30-day slip driven by Apex Fastener Corp quality escape. "
            "240 defective fasteners require removal and replacement "
            "across 12 wing sub-assemblies. Rework plan approved; "
            "recovery depends on replacement fastener delivery by "
            "2024-12-06."
        ),
    },
    {
        "milestone_id": "MS-007",
        "title": "Propulsion System Ground Test",
        "wbs": "1.4",
        "baseline_date": "2025-03-01",
        "forecast_date": "2025-03-01",
        "actual_date": None,
        "slip_days": 0,
        "status": "on_track",
        "is_key_event": True,
        "notes": (
            "Engine integration proceeding nominally. GE F414-EPE test "
            "article delivered and accepted."
        ),
    },
    {
        "milestone_id": "MS-008",
        "title": "Avionics Integration Lab (AIL) Readiness",
        "wbs": "1.5",
        "baseline_date": "2025-04-15",
        "forecast_date": "2025-05-01",
        "actual_date": None,
        "slip_days": 16,
        "status": "at_risk",
        "is_key_event": False,
        "notes": (
            "AESA radar GFE delivery delayed 2 weeks. Recovery plan "
            "targeting April 2025 delivery; 16-day slip if not recovered."
        ),
    },
    {
        "milestone_id": "MS-009",
        "title": "Final Assembly Rollout",
        "wbs": "1.3",
        "baseline_date": "2025-09-30",
        "forecast_date": "2025-10-30",
        "actual_date": None,
        "slip_days": 30,
        "status": "at_risk",
        "is_key_event": True,
        "notes": (
            "Currently projected 30 days late due to Wing Assembly slip "
            "propagation. Critical path runs through MS-006."
        ),
    },
    {
        "milestone_id": "MS-010",
        "title": "First Flight",
        "wbs": "1.7",
        "baseline_date": "2026-03-15",
        "forecast_date": "2026-04-14",
        "actual_date": None,
        "slip_days": 30,
        "status": "at_risk",
        "is_key_event": True,
        "notes": (
            "Directly dependent on Final Assembly Rollout (MS-009). "
            "30-day slip inherited from Wing Assembly critical path. "
            "Flight Test Readiness Review (FTRR) planning underway."
        ),
    },
]

CRITICAL_PATH: dict = {
    "description": (
        "The current critical path runs through the Wing Assembly work "
        "package (WBS 1.3.2). The Apex Fastener Corp quality escape has "
        "inserted 30 days of rework into the critical path, directly "
        "impacting Final Assembly Rollout and First Flight milestones."
    ),
    "critical_path_sequence": [
        {
            "milestone_id": "MS-005",
            "title": "Wing Skin Panel Layup Complete",
            "status": "completed",
        },
        {
            "milestone_id": "MS-006",
            "title": "Wing Assembly Complete",
            "status": "slipped",
            "driving_delay": True,
        },
        {
            "milestone_id": "MS-009",
            "title": "Final Assembly Rollout",
            "status": "at_risk",
        },
        {
            "milestone_id": "MS-010",
            "title": "First Flight",
            "status": "at_risk",
        },
    ],
    "near_critical_paths": [
        {
            "path_name": "Avionics Integration",
            "total_float_days": 12,
            "milestones": ["MS-008", "MS-009", "MS-010"],
            "risk": (
                "AESA radar GFE delay could consume remaining float and "
                "merge with the current critical path."
            ),
        },
    ],
    "schedule_margin": {
        "program_end_baseline": "2027-06-30",
        "program_end_forecast": "2027-07-30",
        "total_margin_remaining_days": -30,
        "assessment": (
            "Program is currently projecting a 30-day breach of the "
            "contractual completion date. Recovery options under evaluation "
            "include overtime authorization and parallel processing of "
            "wing sub-assemblies."
        ),
    },
}
