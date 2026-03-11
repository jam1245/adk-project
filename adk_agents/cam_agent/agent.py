"""
CAM Agent for ADK Web UI (refactored).

Routes EVM and cost performance queries to the external CAM assistant via
the LM platform API.  Uses native ADK sub_agents pattern -- this agent is a
peer sub-agent under the orchestrator.
"""

import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import os
from google.adk.agents import LlmAgent
from src.tools.external_assistant_tool import call_cam_assistant_v2
from src.tools.placeholder_tools import get_program_context, format_output, log_agent_action
from src.config.model_config import get_model
# New import to fetch dynamic description from Genesis API
from src.tools.genesis_description import fetch_description


# Alias retained for backward compatibility – original name now points to the v2 implementation.
def call_cam_assistant(query: str) -> dict:
    return call_cam_assistant_v2(query)


# Resolve the assistant description at import time.  If the API call fails we fall
# back to the original static description to ensure the agent can still be
# instantiated.
_CAM_DESCRIPTION_FALLBACK = (
    "Handles EVM and cost performance questions: CPI/SPI analysis, cost variance, "
    "EAC projections, budget performance, and earned value metrics."
)
_CAM_DESCRIPTION = fetch_description(
    os.getenv("CAM_ASSISTANT_ID"), fallback=_CAM_DESCRIPTION_FALLBACK
)

cam_agent = LlmAgent(
    name="cam_agent",
    model=get_model(),
    description=_CAM_DESCRIPTION,
    instruction="""You are the CAM Agent, a specialist in earned value management and cost performance.

Your primary job is to call the external CAM assistant using the call_cam_assistant tool.
Pass the user's full query to it and return its response clearly and directly.

Use get_program_context if you need basic program metadata before calling the assistant.
Use format_output to clean up the response before returning it.
Use log_agent_action to record significant actions.

IMPORTANT - error handling:
- If call_cam_assistant returns a result with status "error", tell the user what went wrong
  and that the external assistant is temporarily unavailable.
- Do NOT silently transfer to another agent. You own this request.
- You may offer to retry the call if the error seems transient (timeout, connection error).
- Only if the user explicitly asks for a different type of analysis (e.g. risk, root cause)
  should the request go to a different agent.""",
    tools=[call_cam_assistant, get_program_context, format_output, log_agent_action]
)

root_agent = cam_agent  # Required for ADK web UI standalone discovery
