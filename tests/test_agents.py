"""
Unit tests for specialist agents.
"""

import pytest
from unittest.mock import MagicMock, patch

from google.adk.models.lite_llm import LiteLlm

from src.agents.pm_agent import create_pm_agent, PM_SYSTEM_PROMPT
from src.agents.cam_agent import create_cam_agent, CAM_SYSTEM_PROMPT
from src.agents.rca_agent import create_rca_agent, RCA_SYSTEM_PROMPT
from src.agents.risk_agent import create_risk_agent, RISK_SYSTEM_PROMPT
from src.agents.contracts_agent import create_contracts_agent, CONTRACTS_SYSTEM_PROMPT
from src.agents.sq_agent import create_sq_agent, SQ_SYSTEM_PROMPT
from src.tools.tool_registry import ToolRegistry

# Expected model used by all agents
EXPECTED_MODEL = "anthropic/claude-3-haiku-20240307"


def check_agent_model(agent):
    """Helper to verify agent uses the expected LiteLlm model."""
    assert isinstance(agent.model, LiteLlm), "Agent model should be LiteLlm instance"
    assert agent.model.model == EXPECTED_MODEL, f"Expected model {EXPECTED_MODEL}"


class TestAgentCreation:
    """Test agent creation and configuration."""

    def test_create_pm_agent(self):
        """Test PM agent creation."""
        registry = ToolRegistry()
        agent = create_pm_agent(registry)

        assert agent.name == "pm_agent"
        check_agent_model(agent)
        assert agent.instruction == PM_SYSTEM_PROMPT
        assert len(agent.tools) > 0

    def test_create_cam_agent(self):
        """Test CAM agent creation."""
        registry = ToolRegistry()
        agent = create_cam_agent(registry)

        assert agent.name == "cam_agent"
        check_agent_model(agent)
        assert agent.instruction == CAM_SYSTEM_PROMPT
        assert len(agent.tools) > 0

    def test_create_rca_agent(self):
        """Test RCA agent creation."""
        registry = ToolRegistry()
        agent = create_rca_agent(registry)

        assert agent.name == "rca_agent"
        check_agent_model(agent)
        assert agent.instruction == RCA_SYSTEM_PROMPT
        assert len(agent.tools) > 0

    def test_create_risk_agent(self):
        """Test Risk agent creation."""
        registry = ToolRegistry()
        agent = create_risk_agent(registry)

        assert agent.name == "risk_agent"
        check_agent_model(agent)
        assert agent.instruction == RISK_SYSTEM_PROMPT
        assert len(agent.tools) > 0

    def test_create_contracts_agent(self):
        """Test Contracts agent creation."""
        registry = ToolRegistry()
        agent = create_contracts_agent(registry)

        assert agent.name == "contracts_agent"
        check_agent_model(agent)
        assert agent.instruction == CONTRACTS_SYSTEM_PROMPT
        assert len(agent.tools) > 0

    def test_create_sq_agent(self):
        """Test S/Q agent creation."""
        registry = ToolRegistry()
        agent = create_sq_agent(registry)

        assert agent.name == "sq_agent"
        check_agent_model(agent)
        assert agent.instruction == SQ_SYSTEM_PROMPT
        assert len(agent.tools) > 0

    def test_agents_have_unique_names(self):
        """Test that all agents have unique names."""
        registry = ToolRegistry()
        agents = [
            create_pm_agent(registry),
            create_cam_agent(registry),
            create_rca_agent(registry),
            create_risk_agent(registry),
            create_contracts_agent(registry),
            create_sq_agent(registry),
        ]
        names = [a.name for a in agents]
        assert len(names) == len(set(names)), "Agent names must be unique"

    def test_agent_without_registry(self):
        """Test that agents can be created without providing a registry."""
        agent = create_pm_agent()
        assert agent is not None
        assert agent.name == "pm_agent"


class TestAgentSystemPrompts:
    """Test agent system prompts contain required elements."""

    def test_pm_prompt_has_what_why_structure(self):
        """Test PM prompt includes What/Why/So What/Now What."""
        assert "WHAT HAPPENED" in PM_SYSTEM_PROMPT
        assert "WHY IT HAPPENED" in PM_SYSTEM_PROMPT
        assert "SO WHAT" in PM_SYSTEM_PROMPT
        assert "NOW WHAT" in PM_SYSTEM_PROMPT

    def test_cam_prompt_has_evm_elements(self):
        """Test CAM prompt includes EVM terminology."""
        assert "CPI" in CAM_SYSTEM_PROMPT
        assert "SPI" in CAM_SYSTEM_PROMPT
        assert "EAC" in CAM_SYSTEM_PROMPT
        assert "variance" in CAM_SYSTEM_PROMPT.lower()

    def test_rca_prompt_has_5_whys(self):
        """Test RCA prompt includes 5 Whys methodology."""
        assert "5 Whys" in RCA_SYSTEM_PROMPT or "Why 1" in RCA_SYSTEM_PROMPT

    def test_risk_prompt_has_5x5_matrix(self):
        """Test Risk prompt includes 5x5 risk matrix."""
        assert "5x5" in RISK_SYSTEM_PROMPT

    def test_contracts_prompt_has_far_references(self):
        """Test Contracts prompt includes FAR/DFARS."""
        assert "FAR" in CONTRACTS_SYSTEM_PROMPT
        assert "DFARS" in CONTRACTS_SYSTEM_PROMPT

    def test_sq_prompt_has_quality_metrics(self):
        """Test S/Q prompt includes quality metrics."""
        assert "OTDP" in SQ_SYSTEM_PROMPT or "On-Time Delivery" in SQ_SYSTEM_PROMPT
        assert "DPMO" in SQ_SYSTEM_PROMPT


class TestAgentToolAssignment:
    """Test that agents have appropriate tools assigned."""

    def test_pm_agent_has_artifact_tools(self):
        """Test PM agent has all artifact generation tools."""
        registry = ToolRegistry()
        agent = create_pm_agent(registry)
        tool_names = [t.func.__name__ for t in agent.tools]

        assert "write_leadership_brief" in tool_names
        assert "write_cam_narrative" in tool_names
        assert "write_risk_register_update" in tool_names

    def test_cam_agent_has_evm_tools(self):
        """Test CAM agent has EVM analysis tools."""
        registry = ToolRegistry()
        agent = create_cam_agent(registry)
        tool_names = [t.func.__name__ for t in agent.tools]

        assert "read_evm_metrics" in tool_names
        assert "read_evm_history" in tool_names
        assert "calculate_eac" in tool_names

    def test_rca_agent_has_investigation_tools(self):
        """Test RCA agent has investigation tools."""
        registry = ToolRegistry()
        agent = create_rca_agent(registry)
        tool_names = [t.func.__name__ for t in agent.tools]

        assert "read_quality_escape_data" in tool_names
        assert "write_eight_d_report" in tool_names

    def test_risk_agent_has_risk_tools(self):
        """Test Risk agent has risk management tools."""
        registry = ToolRegistry()
        agent = create_risk_agent(registry)
        tool_names = [t.func.__name__ for t in agent.tools]

        assert "read_risk_register" in tool_names
        assert "calculate_risk_exposure" in tool_names
        assert "write_risk_register_update" in tool_names

    def test_contracts_agent_has_contract_tools(self):
        """Test Contracts agent has contract management tools."""
        registry = ToolRegistry()
        agent = create_contracts_agent(registry)
        tool_names = [t.func.__name__ for t in agent.tools]

        assert "read_contract_baseline" in tool_names
        assert "read_contract_mods" in tool_names
        assert "assess_contract_mod_impact" in tool_names

    def test_sq_agent_has_supplier_tools(self):
        """Test S/Q agent has supplier management tools."""
        registry = ToolRegistry()
        agent = create_sq_agent(registry)
        tool_names = [t.func.__name__ for t in agent.tools]

        assert "read_supplier_metrics" in tool_names
        assert "assess_supplier_risk" in tool_names
        assert "calculate_cost_of_poor_quality" in tool_names
