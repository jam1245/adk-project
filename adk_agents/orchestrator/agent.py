"""
Orchestrator Agent for ADK Web UI (refactored).

Routes program management requests to the appropriate
specialist sub-agent using ADK's native sub_agents delegation pattern.
Sub-agents take full control of their domain; the orchestrator never answers
directly from its own knowledge.
"""

import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from google.adk.agents import LlmAgent

# Import all four sub-agents
from adk_agents.pm_agent.agent import pm_agent
from adk_agents.risk_agent.agent import risk_agent
from adk_agents.rcca_agent.agent import rcca_agent
from adk_agents.cam_agent.agent import cam_agent

# Import centralized model configuration
from src.config.model_config import get_model

# IMPORTANT: sub_agents — NOT tools. This is native ADK agent handoff, not tool-calling.
orchestrator = LlmAgent(
    name="orchestrator",
    model=get_model(),
    description="Program Execution Workbench orchestrator. Routes program management requests to the appropriate specialist sub-agent.",
    instruction="""You are the Program Execution Workbench orchestrator, a multi-agent system for program management.

Your ONLY job is to route incoming requests to the correct specialist sub-agent.

Do NOT answer questions directly from your own knowledge. Always delegate.

Routing guide:
- pm_agent:   leadership briefs, executive summaries, schedule status, milestones, program health, what/why/so-what
- risk_agent: risk identification, mitigation, risk register, risk exposure, probability/impact, 5x5 matrix
- rcca_agent: root cause analysis, corrective actions, 5 Whys, Fishbone, 8D problem-solving, systemic issues
- cam_agent:  EVM metrics, CPI, SPI, cost variance, EAC, budget performance, earned value

Transfer control to the appropriate sub-agent and let them handle the full response.
If a request spans multiple domains, route to the most relevant primary specialist first.""",
    sub_agents=[pm_agent, risk_agent, rcca_agent, cam_agent]
    # ^^^ sub_agents, NOT tools. This is the critical line.
)

root_agent = orchestrator  # Required for ADK web UI discovery
