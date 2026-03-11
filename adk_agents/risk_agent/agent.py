"""
Risk Agent for ADK Web UI (refactored).

Routes risk management queries to the external Risk assistant via the
LM platform API.  Uses native ADK sub_agents pattern -- this agent is a
peer sub-agent under the orchestrator.
"""

import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import os
from google.adk.agents import LlmAgent
from src.tools.external_assistant_tool import call_risk_assistant_v2
from src.tools.placeholder_tools import get_program_context, format_output, log_agent_action
from src.config.model_config import get_model
from src.tools.genesis_description import fetch_description


# Alias retained for backward compatibility – original name now points to the v2 implementation.
def call_risk_assistant(query: str) -> dict:
    return call_risk_assistant_v2(query)


# Fallback static description matching the original.
_RISK_DESCRIPTION_FALLBACK = (
    "Handles risk management questions: risk identification, 5x5 risk matrix, "
    "mitigation planning, risk register updates, and risk exposure calculations."
)
_RISK_DESCRIPTION = fetch_description(
    os.getenv("RISK_ASSISTANT_ID"), fallback=_RISK_DESCRIPTION_FALLBACK
)

risk_agent = LlmAgent(
    name="risk_agent",
    model=get_model(),
    description=_RISK_DESCRIPTION,
    instruction="""You are the Risk Agent, a specialist in program risk management.

Your primary job is to call the external Risk assistant using the call_risk_assistant tool.
Pass the user's full query to it and return its response clearly and directly.

Use get_program_context if you need basic program metadata before calling the assistant.
Use format_output to clean up the response before returning it.
Use log_agent_action to record significant actions.

IMPORTANT - error handling:
- If call_risk_assistant returns a result with status "error", tell the user what went wrong
  and that the external assistant is temporarily unavailable.
- Do NOT silently transfer to another agent. You own this request.
- You may offer to retry the call if the error seems transient (timeout, connection error).
- Only if the user explicitly asks for a different type of analysis (e.g. EVM, root cause)
  should the request go to a different agent.""",
    tools=[call_risk_assistant, get_program_context, format_output, log_agent_action]
)

root_agent = risk_agent  # Required for ADK web UI standalone discovery
