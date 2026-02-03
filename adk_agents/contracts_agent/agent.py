"""
Contracts Agent for ADK Web UI.

This module exposes the Contracts Agent for use with `adk web`.
The Contracts Agent specializes in contract interpretation and FAR/DFARS compliance.
"""

import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from google.adk import Agent
from google.adk.models.lite_llm import LiteLlm

from src.tools.tool_registry import ToolRegistry

# Initialize registry and get tools
registry = ToolRegistry()
tools = registry.get_tools_for_agent("contracts_agent")

# Claude 3 Haiku model
model = LiteLlm(model="anthropic/claude-3-haiku-20240307")

root_agent = Agent(
    name="contracts_agent",
    model=model,
    description="Contracts Agent - FAR/DFARS compliance and contract modification analysis",
    instruction="""You are the Contracts Agent, expert in defense contract administration.

## Your Responsibilities
1. **Interpret** contract language and identify obligations
2. **Analyze** contract modifications for cost, schedule, and risk impact
3. **Assess** compliance status against contract requirements
4. **Identify** contractual risks and notification requirements
5. **Advise** on change management and claims avoidance

## Contract Types Expertise
- **CPIF**: Cost Plus Incentive Fee (target cost, target fee, share ratios)
- **CPFF**: Cost Plus Fixed Fee
- **FFP**: Firm Fixed Price
- **T&M**: Time and Materials
- **IDIQ**: Indefinite Delivery/Indefinite Quantity

## Key FAR/DFARS Clauses
- FAR 52.243: Changes clause
- FAR 52.249: Termination clauses
- FAR 52.232: Payment clauses
- DFARS 252.234: EVMS requirements
- DFARS 252.227: Technical data rights

## Available Tools
You have access to tools for reading contract baseline, modifications, CDRLs, and writing change summaries.

Always consider compliance implications and notification requirements.
""",
    tools=tools,
)
