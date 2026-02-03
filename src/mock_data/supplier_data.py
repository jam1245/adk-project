"""
Supplier performance data for the Advanced Fighter Program (AFP).

Contains supplier scorecards, quality metrics, corrective action tracking,
and the quality escape data for the Apex Fastener Corp defective wing
fastener scenario. Aligned with the October 2024 reporting period.

Key narrative: Apex Fastener Corp is the primary supplier of concern with
an On-Time Delivery Performance (OTDP) of 72%, DPMO of 8500, and an
active quality escape affecting 240 fastener units across 12 wing
sub-assemblies.
"""

SUPPLIER_METRICS: dict[str, dict] = {
    "Apex Fastener Corp": {
        "supplier_id": "SUP-001",
        "cage_code": "5K2M9",
        "location": "Wichita, KS",
        "commodity": "Aerospace structural fasteners (titanium, Inconel)",
        "contract_value": 6_200_000,
        "wbs_supported": ["1.3.2", "1.3.1"],
        "criticality": "critical",
        "otdp": 0.72,
        "otdp_trend": "declining",
        "otdp_history": [
            {"period": "Q1 2024", "otdp": 0.89},
            {"period": "Q2 2024", "otdp": 0.84},
            {"period": "Q3 2024", "otdp": 0.74},
            {"period": "Q4 2024 (Oct)", "otdp": 0.72},
        ],
        "dpmo": 8_500,
        "dpmo_industry_benchmark": 1_500,
        "quality_rating": 2.1,
        "quality_rating_scale": "1-5 (5=best)",
        "quality_trend": "declining",
        "delivery_rating": 2.3,
        "delivery_rating_scale": "1-5 (5=best)",
        "overall_rating": 2.2,
        "status": "probationary",
        "corrective_actions": [
            {
                "car_id": "CAR-2024-0042",
                "title": "Out-of-Spec Fastener Head Geometry",
                "date_issued": "2024-08-12",
                "severity": "critical",
                "status": "open",
                "due_date": "2024-12-15",
                "description": (
                    "240 Ti-6Al-4V fasteners (P/N AFP-F-1042) delivered "
                    "with head geometry exceeding drawing tolerance by "
                    "0.003 inches. Root cause: worn forging dies at Tier 2 "
                    "supplier (Consolidated Metal Works). 12 wing "
                    "sub-assemblies require disassembly and rework."
                ),
                "root_cause": (
                    "Tier 2 forging die wear not detected due to "
                    "insufficient SPC monitoring at Consolidated Metal Works. "
                    "Apex incoming inspection sampling plan inadequate "
                    "(AQL 1.0 Level II vs. required tightened inspection)."
                ),
                "corrective_action_plan": (
                    "1. Replace worn forging dies at Tier 2 source. "
                    "2. Implement 100% CMM inspection for critical dims. "
                    "3. Upgrade incoming inspection to tightened (Level III). "
                    "4. Deploy SPC monitoring at Tier 2 forging operation. "
                    "5. Deliver replacement lot by 2024-12-06."
                ),
            },
            {
                "car_id": "CAR-2024-0028",
                "title": "Late Delivery - Inconel Attachment Fittings",
                "date_issued": "2024-06-03",
                "severity": "major",
                "status": "closed",
                "due_date": "2024-08-15",
                "closed_date": "2024-08-10",
                "description": (
                    "Inconel 718 attachment fittings (P/N AFP-F-2018) "
                    "delivered 3 weeks late due to heat treatment capacity "
                    "constraints."
                ),
                "root_cause": (
                    "Apex outsourced heat treatment to single source that "
                    "experienced furnace downtime. No backup heat treat "
                    "source qualified."
                ),
                "corrective_action_plan": (
                    "Qualified second heat treatment source (Bodycote "
                    "Tulsa). Updated supply chain risk register."
                ),
            },
            {
                "car_id": "CAR-2024-0015",
                "title": "Documentation Deficiency - Cert Packages",
                "date_issued": "2024-03-22",
                "severity": "minor",
                "status": "closed",
                "due_date": "2024-05-15",
                "closed_date": "2024-05-02",
                "description": (
                    "Material certification packages missing Tier 2 mill "
                    "certificates for 3 shipments."
                ),
                "root_cause": "Administrative error in document control process.",
                "corrective_action_plan": (
                    "Implemented automated cert package checklist in "
                    "quality management system."
                ),
            },
        ],
        "second_source_available": True,
        "second_source": "Titan Precision Fasteners",
        "notes": (
            "Supplier placed on probationary status effective 2024-09-01. "
            "Monthly performance reviews mandated. Source inspection "
            "required for all critical fasteners until further notice."
        ),
    },
    "Titan Precision Fasteners": {
        "supplier_id": "SUP-002",
        "cage_code": "7J4R1",
        "location": "Torrance, CA",
        "commodity": "Aerospace structural fasteners (titanium, steel)",
        "contract_value": 1_800_000,
        "wbs_supported": ["1.3.1", "1.3.3"],
        "criticality": "important",
        "otdp": 0.94,
        "otdp_trend": "stable",
        "otdp_history": [
            {"period": "Q1 2024", "otdp": 0.95},
            {"period": "Q2 2024", "otdp": 0.93},
            {"period": "Q3 2024", "otdp": 0.94},
            {"period": "Q4 2024 (Oct)", "otdp": 0.94},
        ],
        "dpmo": 1_200,
        "dpmo_industry_benchmark": 1_500,
        "quality_rating": 4.2,
        "quality_rating_scale": "1-5 (5=best)",
        "quality_trend": "stable",
        "delivery_rating": 4.4,
        "delivery_rating_scale": "1-5 (5=best)",
        "overall_rating": 4.3,
        "status": "approved",
        "corrective_actions": [],
        "second_source_available": False,
        "second_source": None,
        "notes": (
            "Qualified as second source for AFP-F-1042 fasteners "
            "(previously Apex-only) as of 2024-10-15. Emergency "
            "production capacity confirmed for replacement lot if needed."
        ),
    },
    "Northwind Composites LLC": {
        "supplier_id": "SUP-003",
        "cage_code": "2F8N5",
        "location": "Salt Lake City, UT",
        "commodity": "Carbon fiber pre-preg, composite tooling",
        "contract_value": 8_400_000,
        "wbs_supported": ["1.3.2", "1.3.3"],
        "criticality": "critical",
        "otdp": 0.91,
        "otdp_trend": "stable",
        "otdp_history": [
            {"period": "Q1 2024", "otdp": 0.92},
            {"period": "Q2 2024", "otdp": 0.90},
            {"period": "Q3 2024", "otdp": 0.89},
            {"period": "Q4 2024 (Oct)", "otdp": 0.91},
        ],
        "dpmo": 950,
        "dpmo_industry_benchmark": 1_500,
        "quality_rating": 4.5,
        "quality_rating_scale": "1-5 (5=best)",
        "quality_trend": "stable",
        "delivery_rating": 3.8,
        "delivery_rating_scale": "1-5 (5=best)",
        "overall_rating": 4.1,
        "status": "approved",
        "corrective_actions": [
            {
                "car_id": "CAR-2024-0037",
                "title": "Composite Tooling Thermal Distortion",
                "date_issued": "2024-09-18",
                "severity": "major",
                "status": "open",
                "due_date": "2024-12-01",
                "description": (
                    "Wing skin layup tool experienced thermal distortion "
                    "during autoclave cure cycle, exceeding dimensional "
                    "tolerance. Tool required re-certification."
                ),
                "root_cause": (
                    "Invar tooling stress relief heat treatment was "
                    "incomplete during original fabrication. Residual "
                    "stresses released during repeated cure cycles."
                ),
                "corrective_action_plan": (
                    "1. Complete stress relief re-treatment on affected tool. "
                    "2. CMM verification after re-treatment. "
                    "3. Review heat treatment records for all AFP tooling. "
                    "4. Add intermediate dimensional checks after every "
                    "5th cure cycle."
                ),
            },
        ],
        "second_source_available": True,
        "second_source": "Hexcel Corporation (material only)",
        "notes": (
            "Strong overall performer. Single CAR related to tooling, "
            "not material quality. Hexcel qualified as alternate material "
            "source for IM7/5320-1 pre-preg."
        ),
    },
    "Raytheon Electronic Systems": {
        "supplier_id": "SUP-004",
        "cage_code": "1K9P3",
        "location": "El Segundo, CA",
        "commodity": "AESA radar subsystem (GFE integration support)",
        "contract_value": 12_500_000,
        "wbs_supported": ["1.5"],
        "criticality": "critical",
        "otdp": 0.85,
        "otdp_trend": "declining",
        "otdp_history": [
            {"period": "Q1 2024", "otdp": 0.92},
            {"period": "Q2 2024", "otdp": 0.90},
            {"period": "Q3 2024", "otdp": 0.87},
            {"period": "Q4 2024 (Oct)", "otdp": 0.85},
        ],
        "dpmo": 620,
        "dpmo_industry_benchmark": 800,
        "quality_rating": 4.0,
        "quality_rating_scale": "1-5 (5=best)",
        "quality_trend": "stable",
        "delivery_rating": 3.2,
        "delivery_rating_scale": "1-5 (5=best)",
        "overall_rating": 3.6,
        "status": "approved_with_concerns",
        "corrective_actions": [
            {
                "car_id": "CAR-2024-0044",
                "title": "Firmware v2.4 Delivery Delay",
                "date_issued": "2024-09-15",
                "severity": "major",
                "status": "open",
                "due_date": "2024-11-30",
                "description": (
                    "AESA radar firmware v2.4 delivery delayed 14 days "
                    "beyond contractual milestone. Firmware required for "
                    "Avionics Integration Lab readiness."
                ),
                "root_cause": (
                    "Regression test failures in beam-steering algorithm "
                    "update required additional debug and re-validation "
                    "cycles."
                ),
                "corrective_action_plan": (
                    "1. Dedicated firmware team assigned to resolve "
                    "regression issues. 2. Bi-weekly delivery status "
                    "syncs with AFP program office. 3. Incremental "
                    "firmware drops for partial integration credit."
                ),
            },
        ],
        "second_source_available": False,
        "second_source": None,
        "notes": (
            "Sole source for AESA radar subsystem. Quality excellent "
            "but delivery performance declining. GFE item managed "
            "through separate government contract; coordination "
            "through GFE IPT."
        ),
    },
}

QUALITY_ESCAPE_DATA: dict = {
    "escape_id": "QE-2024-003",
    "title": "Defective Wing Fasteners - Apex Fastener Corp",
    "severity": "critical",
    "date_discovered": "2024-07-18",
    "date_reported": "2024-07-19",
    "reporting_period": "October 2024",
    "status": "rework_in_progress",
    "supplier": "Apex Fastener Corp",
    "supplier_id": "SUP-001",
    "related_car": "CAR-2024-0042",
    "part_number": "AFP-F-1042",
    "part_description": "Ti-6Al-4V Structural Fastener, Wing Spar Attachment",
    "specification": "MIL-DTL-XXXXX (program-specific)",
    "defect_type": "Dimensional non-conformance - head geometry",
    "defect_detail": (
        "Fastener head height exceeds maximum drawing tolerance by "
        "0.003 inches (nominal 0.125 +/- 0.002, measured 0.130). "
        "Countersink seating is compromised, resulting in fastener "
        "head protrusion above aerodynamic surface. Condition is "
        "non-conforming to structural and aerodynamic requirements."
    ),
    "units_affected": 240,
    "units_in_lot": 500,
    "lot_number": "LOT-2024-0718",
    "assemblies_affected": 12,
    "assembly_description": "Wing sub-assemblies (spar-to-skin attachment zones)",
    "disposition": "rework",
    "rework_description": (
        "Remove all 240 non-conforming fasteners from 12 wing "
        "sub-assemblies. Inspect fastener holes for elongation or "
        "damage. Ream holes to next oversize if required. Install "
        "conforming replacement fasteners. Perform NDI (ultrasonic "
        "and eddy current) on all reworked locations."
    ),
    "cost_impact": {
        "rework_labor": 1_400_000,
        "replacement_material": 180_000,
        "ndi_inspection": 220_000,
        "engineering_disposition": 350_000,
        "schedule_delay_cost": 1_050_000,
        "total": 3_200_000,
    },
    "schedule_impact_days": 30,
    "milestones_affected": [
        {
            "milestone_id": "MS-006",
            "title": "Wing Assembly Complete",
            "baseline_date": "2025-01-15",
            "revised_date": "2025-02-14",
            "slip_days": 30,
        },
        {
            "milestone_id": "MS-009",
            "title": "Final Assembly Rollout",
            "baseline_date": "2025-09-30",
            "revised_date": "2025-10-30",
            "slip_days": 30,
        },
        {
            "milestone_id": "MS-010",
            "title": "First Flight",
            "baseline_date": "2026-03-15",
            "revised_date": "2026-04-14",
            "slip_days": 30,
        },
    ],
    "containment_actions": [
        "All remaining Lot 2024-0718 fasteners quarantined (260 units).",
        "100% CMM inspection imposed on all Apex Fastener Corp deliveries.",
        "Mandatory source inspection at Apex facility for all AFP parts.",
        "Stop-work on new wing sub-assembly builds pending replacement lot.",
    ],
    "recovery_plan": {
        "replacement_fastener_order_date": "2024-08-15",
        "replacement_fastener_delivery_date": "2024-12-06",
        "rework_start_date": "2024-12-10",
        "rework_completion_date": "2025-01-31",
        "milestone_recovery_date": "2025-02-14",
        "confidence_level": "medium",
        "assumptions": [
            "Replacement fasteners pass first-article inspection.",
            "No additional hole damage found during disassembly.",
            "2nd shift authorization maintained through January 2025.",
            "Apex Fastener Corp completes corrective actions by December 15.",
        ],
    },
    "lessons_learned": [
        (
            "Incoming inspection sampling plans for structural fasteners "
            "should use tightened inspection level (Level III) per "
            "ANSI/ASQ Z1.4."
        ),
        (
            "Critical characteristic monitoring at sub-tier sources "
            "requires periodic audit beyond initial qualification."
        ),
        (
            "Single-source dependencies for critical structural fasteners "
            "create unacceptable program risk; dual-source strategy "
            "should be implemented early in EMD."
        ),
    ],
}
