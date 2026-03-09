"""
CAM Agent for ADK Web UI (refactored).

Routes EVM and cost performance queries to the external CAM assistant via
the LM platform API.  Uses native ADK sub_agents pattern — this agent is a
peer sub-agent under the orchestrator.
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


def call_cam_assistant(query: str) -> str:
    """Call the CAM Assistant on the internal LM platform with a query."""
    return call_external_assistant(
        query=query,
        assistant_id=os.getenv("CAM_ASSISTANT_ID", "cam-assistant-placeholder")
    )


cam_agent = LlmAgent(
    name="cam_agent",
    model="claude-sonnet-4-20250514",
    description=(
        "Handles EVM and cost performance questions: CPI/SPI analysis, cost variance, "
        "EAC projections, budget performance, and earned value metrics."
    ),
    instruction="""You are the CAM Agent, a specialist in earned value management and cost performance.

Your primary job is to call the external CAM assistant using the call_cam_assistant tool.
Pass the user's full query to it and return its response clearly and directly.

Use get_program_context if you need basic program metadata before calling the assistant.
Use format_output to clean up the response before returning it.
Use log_agent_action to record significant actions.

Do not answer from your own knowledge — always call the external CAM assistant.""",
    tools=[call_cam_assistant, get_program_context, format_output, log_agent_action]
)

root_agent = cam_agent  # Required for ADK web UI standalone discovery
