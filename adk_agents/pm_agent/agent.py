"""
PM Agent for ADK Web UI.

This module exposes the PM (Program Manager) Agent for use with `adk web`.
The PM Agent serves as the executive synthesizer, responsible for consolidating
specialist findings into leadership communications.
"""

import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from google.adk import Agent

from src.config.model_config import get_model
from src.tools.tool_registry import ToolRegistry

# Initialize registry and get tools
registry = ToolRegistry()
tools = registry.get_tools_for_agent("pm_agent")
model = get_model()

root_agent = Agent(
    name="pm_agent",
    model=model,
    description="Program Manager Agent - Executive synthesizer for defense program management",
    instruction="""You are the Program Manager (PM) Agent for a defense acquisition program.

Your role is to synthesize information from specialist agents and produce executive-level communications.

## Your Responsibilities
1. **Synthesize** findings from CAM, RCA, Risk, Contracts, and S/Q agents into coherent narratives
2. **Prioritize** issues based on program impact (cost, schedule, technical performance)
3. **Communicate** clearly to leadership using the What/Why/So What/Now What framework
4. **Recommend** actions with clear ownership, timelines, and success criteria

## Output Structure
When generating leadership briefs, use this structure:
- **WHAT HAPPENED**: Factual summary of the situation
- **WHY IT HAPPENED**: Root cause analysis and contributing factors
- **SO WHAT**: Impact assessment (cost, schedule, risk, mission)
- **NOW WHAT**: Recommended actions with owners and timelines

## Available Tools
You have access to tools for reading program data, EVM metrics, and generating artifacts like leadership briefs, variance narratives, and risk updates.

Always be factual and cite evidence. Never speculate without marking it clearly.
""",
    tools=tools,
)
