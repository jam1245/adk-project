"""
Triage workflow implementation using ADK SequentialAgent.

The triage workflow performs initial intake processing:
1. Normalize and validate inputs
2. Classify the intent/trigger type
3. Determine which specialist agents are required
4. Create the initial case file and populate state
"""

from google.adk import Agent
from google.adk.agents import SequentialAgent

from src.config.model_config import get_model
from src.tools.tool_registry import ToolRegistry

# Intent classification patterns
INTENT_PATTERNS = {
    "explain_variance": [
        "variance", "cpi", "spi", "cost variance", "schedule variance",
        "evm", "earned value", "overrun", "underrun", "performance index"
    ],
    "assess_contract_change": [
        "contract", "mod", "modification", "change order", "amendment",
        "bilateral", "unilateral", "cdrl", "deliverable"
    ],
    "supplier_quality_investigation": [
        "quality", "escape", "defect", "nonconformance", "supplier",
        "dpmo", "rejection", "rework", "scrap", "car"
    ],
    "risk_assessment": [
        "risk", "threat", "opportunity", "probability", "impact",
        "mitigation", "contingency", "exposure"
    ],
    "schedule_analysis": [
        "schedule", "milestone", "slip", "delay", "critical path",
        "float", "ims", "timeline"
    ],
}

# Agent requirements by intent
INTENT_AGENT_MAP = {
    "explain_variance": ["cam_agent", "rca_agent", "risk_agent", "pm_agent"],
    "assess_contract_change": ["contracts_agent", "cam_agent", "risk_agent", "pm_agent"],
    "supplier_quality_investigation": ["sq_agent", "rca_agent", "cam_agent", "contracts_agent", "risk_agent", "pm_agent"],
    "risk_assessment": ["risk_agent", "cam_agent", "pm_agent"],
    "schedule_analysis": ["cam_agent", "risk_agent", "pm_agent"],
}


TRIAGE_AGENT_PROMPT = """You are the Triage Agent responsible for initial intake processing of program management requests.

## Your Task
Analyze the incoming request and:
1. Classify the intent (explain_variance, assess_contract_change, supplier_quality_investigation, risk_assessment, schedule_analysis)
2. Extract key parameters from the request
3. Determine which specialist agents should be engaged

## Classification Rules
- **explain_variance**: Requests about CPI/SPI, cost or schedule variances, EVM metrics
- **assess_contract_change**: Requests about contract modifications, new deliverables, scope changes
- **supplier_quality_investigation**: Quality escapes, supplier defects, nonconformances, CARs
- **risk_assessment**: Risk identification, assessment, or mitigation questions
- **schedule_analysis**: Milestone slips, critical path analysis, schedule recovery

## Output Format
Respond with a structured assessment:
```
INTENT: [classified intent]
CONFIDENCE: [high/medium/low]
KEY_PARAMETERS:
- [parameter 1]: [value]
- [parameter 2]: [value]
REQUIRED_AGENTS: [comma-separated list]
RATIONALE: [brief explanation of classification]
```

Be precise and factual. If the intent is unclear, classify as the most likely match with medium/low confidence.
"""


def classify_intent(trigger_text: str) -> tuple[str, float]:
    """Classify the intent from trigger text using keyword matching.

    Parameters
    ----------
    trigger_text : str
        The incoming request or trigger description.

    Returns
    -------
    tuple[str, float]
        The classified intent and confidence score (0-1).
    """
    trigger_lower = trigger_text.lower()
    scores = {}

    for intent, keywords in INTENT_PATTERNS.items():
        score = sum(1 for kw in keywords if kw in trigger_lower)
        scores[intent] = score

    if not scores or max(scores.values()) == 0:
        return "explain_variance", 0.3  # Default fallback

    best_intent = max(scores, key=scores.get)
    max_score = scores[best_intent]

    # Normalize confidence based on keyword matches
    confidence = min(0.9, 0.3 + (max_score * 0.15))

    return best_intent, confidence


def get_required_agents(intent: str) -> list[str]:
    """Get the list of required agents for a given intent.

    Parameters
    ----------
    intent : str
        The classified intent type.

    Returns
    -------
    list[str]
        List of agent names required for this intent.
    """
    return INTENT_AGENT_MAP.get(intent, ["cam_agent", "risk_agent", "pm_agent"])


def create_triage_agent(registry: ToolRegistry | None = None) -> Agent:
    """Create the triage agent for intent classification.

    Parameters
    ----------
    registry : ToolRegistry, optional
        Tool registry (not used by triage agent but kept for consistency).

    Returns
    -------
    Agent
        Configured triage agent.
    """
    return Agent(
        name="triage_agent",
        model=get_model(),
        instruction=TRIAGE_AGENT_PROMPT,
        tools=[],  # Triage agent doesn't need tools
    )


def create_triage_workflow(registry: ToolRegistry | None = None) -> SequentialAgent:
    """Create the triage workflow as a SequentialAgent.

    The workflow consists of a single triage agent that classifies
    the incoming request. In a more complex scenario, this could
    chain multiple preprocessing agents.

    Parameters
    ----------
    registry : ToolRegistry, optional
        Tool registry for agent creation.

    Returns
    -------
    SequentialAgent
        The triage workflow agent.
    """
    triage_agent = create_triage_agent(registry)

    return SequentialAgent(
        name="triage_workflow",
        sub_agents=[triage_agent],
    )
