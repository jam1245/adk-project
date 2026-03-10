"""
PM Agent for ADK Web UI (refactored).

Routes program management queries to the external PM assistant via the
LM platform API.  Uses native ADK sub_agents pattern — this agent is a
peer sub-agent under the orchestrator, not a coordinator.
"""

import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import os
from google.adk.agents import LlmAgent
from src.tools.external_assistant_tool import call_external_assistant
from src.tools.placeholder_tools import get_program_context, format_output, log_agent_action
from src.config.model_config import get_model


def call_pm_assistant(query: str) -> dict:
    """Call the PM Assistant on the internal LM platform with a query.

    Returns a dict with 'status' ('completed' or 'error') and either
    'response' (the assistant's reply) or 'error' (description of failure).
    """
    return call_external_assistant(
        query=query,
        assistant_id=os.getenv("PM_ASSISTANT_ID", "pm-assistant-placeholder")
    )


pm_agent = LlmAgent(
    name="pm_agent",
    model=get_model(),
    description=(
        "Handles program management questions: leadership briefs, executive summaries, "
        "schedule status, milestone tracking, program health, and what/why/so-what analysis."
    ),
    instruction="""You are the PM Agent, a specialist in program management and executive communication.

Your primary job is to call the external PM assistant using the call_pm_assistant tool.
Pass the user's full query to it and return its response clearly and directly.

Use get_program_context if you need basic program metadata before calling the assistant.
Use format_output to clean up the response before returning it.
Use log_agent_action to record significant actions.

IMPORTANT — error handling:
- If call_pm_assistant returns a result with status "error", tell the user what went wrong
  and that the external assistant is temporarily unavailable.
- Do NOT silently transfer to another agent. You own this request.
- You may offer to retry the call if the error seems transient (timeout, connection error).
- Only if the user explicitly asks for a different type of analysis (e.g. risk, EVM)
  should the request go to a different agent.""",
    tools=[call_pm_assistant, get_program_context, format_output, log_agent_action]
)

root_agent = pm_agent  # Required for ADK web UI standalone discovery
