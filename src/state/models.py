"""
Pydantic models for the Program Execution Workbench.

Defines the complete data schema for defense program analysis, including
Earned Value Management metrics, Integrated Master Schedule milestones,
risk register items, contract modifications, supplier performance, and
the multi-agent workbench state that orchestrates analysis across
specialist agents.

All models use Pydantic v2 syntax with proper validation, sensible
defaults, and full JSON serialization support.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, model_validator


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------

class ImpactLevel(str, Enum):
    """Risk impact severity levels aligned with DoD 5x5 risk matrix."""
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class FindingType(str, Enum):
    """Classification of an agent's finding."""
    observation = "observation"
    analysis = "analysis"
    recommendation = "recommendation"
    action = "action"


class ContradictionSeverity(str, Enum):
    """How severely two findings contradict each other."""
    low = "low"
    medium = "medium"
    high = "high"


class MilestoneStatus(str, Enum):
    """Tracking status of an IMS milestone."""
    completed = "completed"
    on_track = "on_track"
    at_risk = "at_risk"
    slipped = "slipped"
    missed = "missed"


class MilestoneCriticality(str, Enum):
    """Criticality designation for a milestone."""
    key_event = "key_event"
    critical_path = "critical_path"
    near_critical = "near_critical"
    normal = "normal"


class RiskStatus(str, Enum):
    """Current disposition of a risk item."""
    active = "active"
    watch = "watch"
    mitigated = "mitigated"
    closed = "closed"
    accepted = "accepted"


class RiskCategory(str, Enum):
    """High-level risk taxonomy for defense programs."""
    technical = "technical"
    schedule = "schedule"
    cost = "cost"
    supply_chain = "supply_chain"
    requirements = "requirements"
    external = "external"
    programmatic = "programmatic"


class ContractModType(str, Enum):
    """Type of contract modification."""
    administrative = "administrative"
    bilateral = "bilateral"
    unilateral = "unilateral"
    supplemental = "supplemental"


class ContractModStatus(str, Enum):
    """Processing status of a contract modification."""
    proposed = "proposed"
    under_negotiation = "under_negotiation"
    executed = "executed"
    withdrawn = "withdrawn"


class WorkbenchStatus(str, Enum):
    """Pipeline stage of the multi-agent workbench."""
    triaging = "triaging"
    analyzing = "analyzing"
    refining = "refining"
    synthesizing = "synthesizing"
    complete = "complete"


class WorkPackageStatus(str, Enum):
    """Health status indicator for a work package."""
    green = "green"
    yellow = "yellow"
    red = "red"


# ---------------------------------------------------------------------------
# Domain Models
# ---------------------------------------------------------------------------

class EVMMetrics(BaseModel):
    """
    Earned Value Management headline metrics for a program or work package.

    All dollar values are in USD. Indices are dimensionless ratios.
    """
    cpi: float = Field(..., description="Cost Performance Index (BCWP / ACWP)")
    spi: float = Field(..., description="Schedule Performance Index (BCWP / BCWS)")
    cv: float = Field(default=0.0, description="Cost Variance in USD (BCWP - ACWP)")
    sv: float = Field(default=0.0, description="Schedule Variance in USD (BCWP - BCWS)")
    bcwp: float = Field(..., description="Budgeted Cost of Work Performed (Earned Value)")
    bcws: float = Field(..., description="Budgeted Cost of Work Scheduled (Planned Value)")
    acwp: float = Field(..., description="Actual Cost of Work Performed")
    eac: float = Field(default=0.0, description="Estimate at Completion in USD")
    bac: float = Field(..., description="Budget at Completion in USD")
    vac: float = Field(default=0.0, description="Variance at Completion in USD (BAC - EAC)")
    tcpi: float = Field(
        default=1.0,
        description="To-Complete Performance Index (BAC-based)",
    )

    model_config = {"json_schema_extra": {"examples": [
        {
            "cpi": 0.87, "spi": 0.88,
            "cv": -2_100_000, "sv": -1_800_000,
            "bcwp": 15_200_000, "bcws": 17_000_000, "acwp": 17_471_264,
            "eac": 557_471_264, "bac": 485_000_000, "vac": -72_471_264,
            "tcpi": 1.15,
        }
    ]}}


class IMSMilestone(BaseModel):
    """
    A single milestone from the Integrated Master Schedule.
    """
    name: str = Field(..., description="Milestone title")
    baseline_date: date = Field(..., description="Original planned date")
    forecast_date: date = Field(..., description="Current projected date")
    actual_date: Optional[date] = Field(
        default=None,
        description="Actual completion date (None if not yet completed)",
    )
    slip_days: int = Field(
        default=0,
        description="Number of days the milestone has slipped from baseline",
    )
    status: MilestoneStatus = Field(
        default=MilestoneStatus.on_track,
        description="Current tracking status",
    )
    criticality: MilestoneCriticality = Field(
        default=MilestoneCriticality.normal,
        description="Criticality designation on the schedule network",
    )


class WorkPackage(BaseModel):
    """
    A WBS-level work package with cost and schedule performance data.
    """
    wbs_id: str = Field(..., description="Work Breakdown Structure element ID (e.g. '1.3.2')")
    name: str = Field(..., description="Work package title")
    budget: float = Field(..., ge=0, description="Budgeted cost for this work package in USD")
    actual_cost: float = Field(default=0.0, ge=0, description="Actual cost incurred to date in USD")
    percent_complete: float = Field(
        default=0.0,
        ge=0.0,
        le=100.0,
        description="Percent complete (0-100)",
    )
    responsible_cam: str = Field(
        default="",
        description="Control Account Manager responsible for this work package",
    )
    status: WorkPackageStatus = Field(
        default=WorkPackageStatus.green,
        description="RAG health status",
    )


class RiskItem(BaseModel):
    """
    A single entry in the program risk register.

    Uses a probability (0-1) and qualitative impact level to compute a
    risk score. The score is probability * impact-weight where impact
    weights are: low=1, medium=5, high=10, critical=20.
    """
    risk_id: str = Field(..., description="Unique risk identifier (e.g. 'R-001')")
    title: str = Field(..., description="Short risk title")
    description: str = Field(default="", description="Detailed risk description")
    probability: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Likelihood of occurrence (0.0 to 1.0)",
    )
    impact_level: ImpactLevel = Field(..., description="Qualitative impact severity")
    risk_score: float = Field(
        default=0.0,
        ge=0.0,
        description="Computed risk score (probability * impact weight)",
    )
    mitigation_plan: str = Field(default="", description="Planned mitigation actions")
    status: RiskStatus = Field(default=RiskStatus.active, description="Current risk disposition")
    owner: str = Field(default="", description="Person accountable for managing this risk")
    category: RiskCategory = Field(
        default=RiskCategory.programmatic,
        description="Risk taxonomy category",
    )

    @model_validator(mode="after")
    def _compute_risk_score_if_zero(self) -> "RiskItem":
        """Auto-compute risk score from probability and impact if not explicitly provided."""
        if self.risk_score == 0.0 and self.probability and self.impact_level:
            weight_map = {
                ImpactLevel.low: 1,
                ImpactLevel.medium: 5,
                ImpactLevel.high: 10,
                ImpactLevel.critical: 20,
            }
            weight = weight_map.get(self.impact_level, 1)
            self.risk_score = round(self.probability * weight, 2)
        return self


class ContractMod(BaseModel):
    """
    A contract modification (administrative or bilateral/unilateral change).
    """
    mod_number: str = Field(..., description="Modification number (e.g. 'P00027')")
    title: str = Field(..., description="Short title for the modification")
    description: str = Field(default="", description="Detailed description of the mod scope")
    mod_type: ContractModType = Field(
        default=ContractModType.bilateral,
        description="Type of modification",
    )
    cost_impact: float = Field(
        default=0.0,
        description="Dollar impact of this modification in USD",
    )
    schedule_impact_weeks: int = Field(
        default=0,
        description="Schedule impact in weeks (positive = extension)",
    )
    new_deliverables: list[str] = Field(
        default_factory=list,
        description="List of new deliverables introduced by this mod",
    )
    status: ContractModStatus = Field(
        default=ContractModStatus.proposed,
        description="Current processing status",
    )


class SupplierMetric(BaseModel):
    """
    Performance metrics for a program supplier.

    OTDP = On-Time Delivery Performance, DPMO = Defects Per Million
    Opportunities.
    """
    supplier_name: str = Field(..., description="Supplier company name")
    otdp_percent: float = Field(
        default=100.0,
        ge=0.0,
        le=100.0,
        description="On-Time Delivery Performance percentage (0-100)",
    )
    dpmo: float = Field(
        default=0.0,
        ge=0.0,
        description="Defects Per Million Opportunities",
    )
    quality_rating: float = Field(
        default=5.0,
        ge=0.0,
        le=5.0,
        description="Quality rating on a 0-5 scale",
    )
    delivery_rating: float = Field(
        default=5.0,
        ge=0.0,
        le=5.0,
        description="Delivery rating on a 0-5 scale",
    )
    corrective_actions_open: int = Field(
        default=0,
        ge=0,
        description="Number of open corrective action requests",
    )


# ---------------------------------------------------------------------------
# Agent / Workbench Models
# ---------------------------------------------------------------------------

class Finding(BaseModel):
    """
    A single finding produced by a specialist agent.
    """
    agent_name: str = Field(..., description="Name of the agent that produced this finding")
    finding_type: FindingType = Field(
        default=FindingType.observation,
        description="Classification of the finding",
    )
    content: str = Field(..., description="The finding text")
    confidence: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Agent's confidence in this finding (0.0 to 1.0)",
    )
    evidence_refs: list[str] = Field(
        default_factory=list,
        description="References to evidence supporting this finding (document IDs, data sources)",
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="When the finding was produced (UTC)",
    )


class Contradiction(BaseModel):
    """
    A detected contradiction between two agent findings.

    The contradiction detection system identifies when agents produce
    conflicting assessments and tracks resolution.
    """
    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique contradiction identifier",
    )
    finding_a: Finding = Field(..., description="First conflicting finding")
    finding_b: Finding = Field(..., description="Second conflicting finding")
    description: str = Field(
        default="",
        description="Human-readable description of the contradiction",
    )
    severity: ContradictionSeverity = Field(
        default=ContradictionSeverity.medium,
        description="How severely the findings conflict",
    )
    resolution: Optional[str] = Field(
        default=None,
        description="Explanation of how the contradiction was resolved (None if unresolved)",
    )
    resolved: bool = Field(
        default=False,
        description="Whether the contradiction has been resolved",
    )


class CaseFile(BaseModel):
    """
    The central case file that frames a workbench analysis session.

    Contains the user's intent, program context, and all domain data
    needed by the specialist agents to perform their analysis.
    """
    case_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique case identifier",
    )
    intent: str = Field(
        default="",
        description="The user's analytical intent or question",
    )
    trigger_description: str = Field(
        default="",
        description="What triggered this analysis (e.g. monthly review, ad-hoc query)",
    )
    program_name: str = Field(
        default="",
        description="Name of the defense program under analysis",
    )
    reporting_period: str = Field(
        default="",
        description="Reporting period for the analysis (e.g. 'October 2024')",
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When this case file was created (UTC)",
    )
    required_agents: list[str] = Field(
        default_factory=list,
        description="List of specialist agent names required for this analysis",
    )

    # Domain data -- all optional since they are populated during triage
    evm_metrics: Optional[EVMMetrics] = Field(
        default=None,
        description="Earned Value Management headline metrics",
    )
    milestones: Optional[list[IMSMilestone]] = Field(
        default=None,
        description="Integrated Master Schedule milestones",
    )
    work_packages: Optional[list[WorkPackage]] = Field(
        default=None,
        description="WBS-level work packages with performance data",
    )
    risks: Optional[list[RiskItem]] = Field(
        default=None,
        description="Program risk register items",
    )
    contract_mods: Optional[list[ContractMod]] = Field(
        default=None,
        description="Contract modifications",
    )
    supplier_metrics: Optional[list[SupplierMetric]] = Field(
        default=None,
        description="Supplier performance metrics",
    )


class AgentOutput(BaseModel):
    """
    The collected output from a single specialist agent's execution.
    """
    agent_name: str = Field(..., description="Name of the agent that produced this output")
    findings: list[Finding] = Field(
        default_factory=list,
        description="List of findings produced by the agent",
    )
    overall_confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Agent's overall confidence in its analysis (0.0 to 1.0)",
    )
    execution_time_ms: float = Field(
        default=0.0,
        ge=0.0,
        description="Wall-clock execution time in milliseconds",
    )
    tool_calls_made: int = Field(
        default=0,
        ge=0,
        description="Number of tool invocations made during execution",
    )
    errors: list[str] = Field(
        default_factory=list,
        description="Any errors encountered during agent execution",
    )


class WorkbenchState(BaseModel):
    """
    Top-level state object for the multi-agent Program Execution Workbench.

    Tracks the full lifecycle of an analysis session: from initial triage
    through parallel agent execution, contradiction resolution, and
    leadership brief synthesis.
    """
    case_file: CaseFile = Field(..., description="The case file framing this analysis")
    agent_outputs: dict[str, AgentOutput] = Field(
        default_factory=dict,
        description="Mapping of agent name to its output (populated during analysis)",
    )
    contradictions: list[Contradiction] = Field(
        default_factory=list,
        description="Contradictions detected between agent findings",
    )
    leadership_brief: Optional[str] = Field(
        default=None,
        description="Synthesized leadership brief (populated during synthesis phase)",
    )
    artifacts: dict[str, str] = Field(
        default_factory=dict,
        description="Named artifacts produced during analysis (key=name, value=content)",
    )
    status: WorkbenchStatus = Field(
        default=WorkbenchStatus.triaging,
        description="Current pipeline stage of the workbench",
    )
    iteration_count: int = Field(
        default=0,
        ge=0,
        description="Number of refinement iterations completed",
    )
