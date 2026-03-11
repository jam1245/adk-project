"""
RCCA Agent for ADK Web UI.

Routes root cause and corrective action queries to the external RCCA
assistant via the LM platform API.  Uses native ADK sub_agents pattern --
this agent is a peer sub-agent under the orchestrator.
"""

import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import os
from google.adk.agents import LlmAgent
from src.tools.external_assistant_tool import call_rcca_assistant_v2
from src.tools.placeholder_tools import get_program_context, format_output, log_agent_action
from src.config.model_config import get_model
from src.tools.genesis_description import fetch_description


# Alias retained for backward compatibility – original name now points to the v2 implementation.
def call_rcca_assistant(query: str) -> dict:
    return call_rcca_assistant_v2(query)


# Fallback description 
_RCCA_DESCRIPTION_FALLBACK = (
    "Handles root cause and corrective action questions: 5 Whys, Fishbone diagrams, "
    "8D problem-solving, corrective action plans, and systemic issue investigation."
)
_RCCA_DESCRIPTION = fetch_description(
    os.getenv("RCCA_ASSISTANT_ID"), fallback=_RCCA_DESCRIPTION_FALLBACK
)

rcca_agent = LlmAgent(
    name="rcca_agent",
    model=get_model(),
    description=_RCCA_DESCRIPTION,
    instruction="""You are the RCCA Agent, a specialist in root cause analysis and corrective actions.

Your primary job is to call the external RCCA assistant using the call_rcca_assistant tool.
Pass the user's full query to it and return its response clearly and directly.

Use get_program_context if you need basic program metadata before calling the assistant.
Use format_output to clean up the response before returning it.
Use log_agent_action to record significant actions.

IMPORTANT - error handling:
- If call_rcca_assistant returns a result with status "error", tell the user what went wrong
  and that the external assistant is temporarily unavailable.
- Do NOT silently transfer to another agent. You own this request.
- You may offer to retry the call if the error seems transient (timeout, connection error).
- Only if the user explicitly asks for a different type of analysis (e.g. risk, EVM)
  should the request go to a different agent.""",
    tools=[call_rcca_assistant, get_program_context, format_output, log_agent_action]
)

root_agent = rcca_agent  # Required for ADK web UI standalone discovery
