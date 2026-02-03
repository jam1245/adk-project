"""
End-to-end scenario tests for the Program Execution Workbench.
"""

import pytest
import asyncio

from src.workflows.orchestrator import create_orchestrator
from demos.scenario_1_variance import (
    SCENARIO_TRIGGER as VARIANCE_TRIGGER,
    get_scenario_context as get_variance_context,
    validate_outputs as validate_variance,
)
from demos.scenario_2_contract_change import (
    SCENARIO_TRIGGER as CONTRACT_TRIGGER,
    get_scenario_context as get_contract_context,
    validate_outputs as validate_contract,
)
from demos.scenario_3_quality_escape import (
    SCENARIO_TRIGGER as QUALITY_TRIGGER,
    get_scenario_context as get_quality_context,
    validate_outputs as validate_quality,
)


class TestScenario1Variance:
    """End-to-end tests for Scenario 1: Variance Explanation."""

    @pytest.fixture
    def orchestrator(self):
        """Create orchestrator for tests."""
        return create_orchestrator()

    @pytest.mark.asyncio
    async def test_scenario_1_executes(self, orchestrator):
        """Test that scenario 1 executes without errors."""
        result = await orchestrator.run(
            trigger=VARIANCE_TRIGGER,
            user_id="test_user",
            context=get_variance_context(),
        )

        assert result is not None
        assert "case_file" in result
        assert "findings" in result

    @pytest.mark.asyncio
    async def test_scenario_1_correct_intent(self, orchestrator):
        """Test scenario 1 classifies intent correctly."""
        result = await orchestrator.run(
            trigger=VARIANCE_TRIGGER,
            user_id="test_user",
        )

        assert result["case_file"]["intent"] == "explain_variance"

    @pytest.mark.asyncio
    async def test_scenario_1_engages_cam_agent(self, orchestrator):
        """Test scenario 1 engages CAM agent for EVM analysis."""
        result = await orchestrator.run(
            trigger=VARIANCE_TRIGGER,
            user_id="test_user",
        )

        required_agents = result["case_file"]["required_agents"]
        assert "cam_agent" in required_agents

    @pytest.mark.asyncio
    async def test_scenario_1_engages_rca_agent(self, orchestrator):
        """Test scenario 1 engages RCA agent for root cause analysis."""
        result = await orchestrator.run(
            trigger=VARIANCE_TRIGGER,
            user_id="test_user",
        )

        required_agents = result["case_file"]["required_agents"]
        assert "rca_agent" in required_agents

    @pytest.mark.asyncio
    async def test_scenario_1_generates_trace(self, orchestrator):
        """Test scenario 1 generates execution trace."""
        result = await orchestrator.run(
            trigger=VARIANCE_TRIGGER,
            user_id="test_user",
        )

        assert result["trace_id"] is not None
        assert "execution_report" in result

    @pytest.mark.asyncio
    async def test_scenario_1_validation_passes(self, orchestrator):
        """Test scenario 1 passes validation checks."""
        result = await orchestrator.run(
            trigger=VARIANCE_TRIGGER,
            user_id="test_user",
        )

        validation = validate_variance(result)
        assert validation["trace_generated"] is True


class TestScenario2ContractChange:
    """End-to-end tests for Scenario 2: Contract Change Assessment."""

    @pytest.fixture
    def orchestrator(self):
        """Create orchestrator for tests."""
        return create_orchestrator()

    @pytest.mark.asyncio
    async def test_scenario_2_executes(self, orchestrator):
        """Test that scenario 2 executes without errors."""
        result = await orchestrator.run(
            trigger=CONTRACT_TRIGGER,
            user_id="test_user",
            context=get_contract_context(),
        )

        assert result is not None
        assert "case_file" in result

    @pytest.mark.asyncio
    async def test_scenario_2_correct_intent(self, orchestrator):
        """Test scenario 2 classifies intent correctly."""
        result = await orchestrator.run(
            trigger=CONTRACT_TRIGGER,
            user_id="test_user",
        )

        assert result["case_file"]["intent"] == "assess_contract_change"

    @pytest.mark.asyncio
    async def test_scenario_2_engages_contracts_agent(self, orchestrator):
        """Test scenario 2 engages Contracts agent."""
        result = await orchestrator.run(
            trigger=CONTRACT_TRIGGER,
            user_id="test_user",
        )

        required_agents = result["case_file"]["required_agents"]
        assert "contracts_agent" in required_agents

    @pytest.mark.asyncio
    async def test_scenario_2_validation_passes(self, orchestrator):
        """Test scenario 2 passes validation checks."""
        result = await orchestrator.run(
            trigger=CONTRACT_TRIGGER,
            user_id="test_user",
        )

        validation = validate_contract(result)
        assert validation["trace_generated"] is True


class TestScenario3QualityEscape:
    """End-to-end tests for Scenario 3: Quality Escape Investigation."""

    @pytest.fixture
    def orchestrator(self):
        """Create orchestrator for tests."""
        return create_orchestrator()

    @pytest.mark.asyncio
    async def test_scenario_3_executes(self, orchestrator):
        """Test that scenario 3 executes without errors."""
        result = await orchestrator.run(
            trigger=QUALITY_TRIGGER,
            user_id="test_user",
            context=get_quality_context(),
        )

        assert result is not None
        assert "case_file" in result

    @pytest.mark.asyncio
    async def test_scenario_3_correct_intent(self, orchestrator):
        """Test scenario 3 classifies intent correctly."""
        result = await orchestrator.run(
            trigger=QUALITY_TRIGGER,
            user_id="test_user",
        )

        assert result["case_file"]["intent"] == "supplier_quality_investigation"

    @pytest.mark.asyncio
    async def test_scenario_3_engages_sq_agent(self, orchestrator):
        """Test scenario 3 engages S/Q agent."""
        result = await orchestrator.run(
            trigger=QUALITY_TRIGGER,
            user_id="test_user",
        )

        required_agents = result["case_file"]["required_agents"]
        assert "sq_agent" in required_agents

    @pytest.mark.asyncio
    async def test_scenario_3_engages_rca_agent(self, orchestrator):
        """Test scenario 3 engages RCA agent for 8D investigation."""
        result = await orchestrator.run(
            trigger=QUALITY_TRIGGER,
            user_id="test_user",
        )

        required_agents = result["case_file"]["required_agents"]
        assert "rca_agent" in required_agents

    @pytest.mark.asyncio
    async def test_scenario_3_engages_risk_agent(self, orchestrator):
        """Test scenario 3 engages Risk agent for escalation."""
        result = await orchestrator.run(
            trigger=QUALITY_TRIGGER,
            user_id="test_user",
        )

        required_agents = result["case_file"]["required_agents"]
        assert "risk_agent" in required_agents

    @pytest.mark.asyncio
    async def test_scenario_3_validation_passes(self, orchestrator):
        """Test scenario 3 passes validation checks."""
        result = await orchestrator.run(
            trigger=QUALITY_TRIGGER,
            user_id="test_user",
        )

        validation = validate_quality(result)
        assert validation["trace_generated"] is True


class TestCrossScenario:
    """Cross-scenario integration tests."""

    @pytest.fixture
    def orchestrator(self):
        """Create orchestrator for tests."""
        return create_orchestrator()

    @pytest.mark.asyncio
    async def test_all_scenarios_produce_leadership_briefs(self, orchestrator):
        """Test that all scenarios produce leadership briefs."""
        triggers = [VARIANCE_TRIGGER, CONTRACT_TRIGGER, QUALITY_TRIGGER]

        for trigger in triggers:
            result = await orchestrator.run(
                trigger=trigger,
                user_id="test_user",
            )
            assert "leadership_brief" in result
            assert result["leadership_brief"] is not None

    @pytest.mark.asyncio
    async def test_all_scenarios_detect_contradictions(self, orchestrator):
        """Test that contradiction detection runs for all scenarios."""
        triggers = [VARIANCE_TRIGGER, CONTRACT_TRIGGER, QUALITY_TRIGGER]

        for trigger in triggers:
            result = await orchestrator.run(
                trigger=trigger,
                user_id="test_user",
            )
            # Contradictions should be a list (may be empty)
            assert isinstance(result["contradictions"], list)

    @pytest.mark.asyncio
    async def test_orchestrator_reuse(self, orchestrator):
        """Test that orchestrator can be reused across scenarios."""
        # Run first scenario
        result1 = await orchestrator.run(
            trigger=VARIANCE_TRIGGER,
            user_id="user1",
        )

        # Run second scenario
        result2 = await orchestrator.run(
            trigger=CONTRACT_TRIGGER,
            user_id="user2",
        )

        # Both should complete successfully
        assert result1["trace_id"] != result2["trace_id"]
        assert result1["case_file"]["intent"] != result2["case_file"]["intent"]


class TestEdgeCases:
    """Test edge cases and error handling."""

    @pytest.fixture
    def orchestrator(self):
        """Create orchestrator for tests."""
        return create_orchestrator()

    @pytest.mark.asyncio
    async def test_empty_trigger(self, orchestrator):
        """Test handling of empty trigger."""
        result = await orchestrator.run(
            trigger="",
            user_id="test_user",
        )

        # Should still complete with default intent
        assert "case_file" in result

    @pytest.mark.asyncio
    async def test_very_long_trigger(self, orchestrator):
        """Test handling of very long trigger text."""
        long_trigger = "Test variance " * 1000  # Very long input

        result = await orchestrator.run(
            trigger=long_trigger,
            user_id="test_user",
        )

        assert "case_file" in result

    @pytest.mark.asyncio
    async def test_special_characters_in_trigger(self, orchestrator):
        """Test handling of special characters in trigger."""
        trigger = "CPI=$0.87 & SPI<0.90 @milestone #risk"

        result = await orchestrator.run(
            trigger=trigger,
            user_id="test_user",
        )

        assert "case_file" in result
