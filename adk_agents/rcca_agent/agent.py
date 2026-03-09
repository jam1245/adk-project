"""
RCCA Agent for ADK Web UI.

Routes root cause and corrective action queries to the external RCCA
assistant via the LM platform API.  Uses native ADK sub_agents pattern —
this agent is a peer sub-agent under the orchestrator.
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


def call_rcca_assistant(query: str) -> str:
    """Call the RCCA Assistant on the internal LM platform with a query."""
    return call_external_assistant(
        query=query,
        assistant_id=os.getenv("RCCA_ASSISTANT_ID", "rcca-assistant-placeholder")
    )


rcca_agent = LlmAgent(
    name="rcca_agent",
    model="claude-sonnet-4-20250514",
    description=(
        "Handles root cause and corrective action questions: 5 Whys, Fishbone diagrams, "
        "8D problem-solving, corrective action plans, and systemic issue investigation."
    ),
    instruction="""You are the RCCA Agent, a specialist in root cause analysis and corrective actions.

Your primary job is to call the external RCCA assistant using the call_rcca_assistant tool.
Pass the user's full query to it and return its response clearly and directly.

Use get_program_context if you need basic program metadata before calling the assistant.
Use format_output to clean up the response before returning it.
Use log_agent_action to record significant actions.

Do not answer from your own knowledge — always call the external RCCA assistant.""",
    tools=[call_rcca_assistant, get_program_context, format_output, log_agent_action]
)

root_agent = rcca_agent  # Required for ADK web UI standalone discovery
