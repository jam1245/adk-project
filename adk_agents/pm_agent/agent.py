"""
PM Agent for ADK Web UI (refactored).

Routes program management queries to the external PM assistant via the
LM platform API.  Uses native ADK sub_agents pattern -- this agent is a
peer sub-agent under the orchestrator, not a coordinator.
"""

import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import os
from google.adk.agents import LlmAgent
from src.tools.external_assistant_tool import call_pm_assistant_v2
from src.tools.placeholder_tools import get_program_context, format_output, log_agent_action
from src.config.model_config import get_model
from src.tools.genesis_description import fetch_description


# Alias retained for backward compatibility – original name now points to the v2 implementation.
def call_pm_assistant(query: str) -> dict:
    return call_pm_assistant_v2(query)


# Fallback static description used if the API lookup fails.
_PM_DESCRIPTION_FALLBACK = (
    "Handles program management questions: leadership briefs, executive summaries, "
    "schedule status, milestone tracking, program health, and what/why/so-what analysis."
)
_PM_DESCRIPTION = fetch_description(
    os.getenv("PM_ASSISTANT_ID"), fallback=_PM_DESCRIPTION_FALLBACK
)

pm_agent = LlmAgent(
    name="pm_agent",
    model=get_model(),
    description=_PM_DESCRIPTION,
    instruction="""You are the PM Agent, a specialist in program management and executive communication.

Your primary job is to call the external PM assistant using the call_pm_assistant tool.
Pass the user's full query to it and return its response clearly and directly.

Use get_program_context if you need basic program metadata before calling the assistant.
Use format_output to clean up the response before returning it.
Use log_agent_action to record significant actions.

IMPORTANT - error handling:
- If call_pm_assistant returns a result with status "error", tell the user what went wrong
  and that the external assistant is temporarily unavailable.
- Do NOT silently transfer to another agent. You own this request.
- You may offer to retry the call if the error seems transient (timeout, connection error).
- Only if the user explicitly asks for a different type of analysis (e.g. risk, EVM)
  should the request go to a different agent.""",
    tools=[call_pm_assistant, get_program_context, format_output, log_agent_action]
)

root_agent = pm_agent  # Required for ADK web UI standalone discovery
