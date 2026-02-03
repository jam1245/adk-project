"""
Unit tests for tools.
"""

import pytest
from src.tools.data_tools import (
    read_program_snapshot,
    read_evm_metrics,
    read_evm_history,
    read_ims_milestones,
    read_risk_register,
    read_contract_baseline,
    read_contract_mods,
    read_supplier_metrics,
    read_quality_escape_data,
    read_cdrl_list,
)
from src.tools.analysis_tools import (
    calculate_eac,
    calculate_variance_drivers,
    analyze_cpi_trend,
    calculate_risk_exposure,
    assess_supplier_risk,
    calculate_cost_of_poor_quality,
    assess_contract_mod_impact,
)
from src.tools.tool_registry import ToolRegistry


class TestDataTools:
    """Test data retrieval tools."""

    def test_read_program_snapshot(self):
        """Test reading program snapshot."""
        result = read_program_snapshot()

        assert "error" not in result
        assert result["program_name"] == "Advanced Fighter Program (AFP)"
        assert "contract_number" in result
        assert "budget_at_completion" in result

    def test_read_evm_metrics(self):
        """Test reading EVM metrics."""
        result = read_evm_metrics()

        assert "error" not in result
        assert "CPI" in result
        assert "SPI" in result
        assert result["CPI"] == 0.87
        assert result["SPI"] == 0.88
        assert "work_packages" in result

    def test_read_evm_history(self):
        """Test reading EVM history."""
        result = read_evm_history()

        assert "error" not in result
        assert "periods" in result
        assert result["period_count"] >= 6
        assert result["earliest_period"] is not None

    def test_read_ims_milestones(self):
        """Test reading IMS milestones."""
        result = read_ims_milestones()

        assert "error" not in result
        assert "milestones" in result
        assert result["milestone_count"] >= 8
        assert "critical_path" in result

    def test_read_risk_register(self):
        """Test reading risk register."""
        result = read_risk_register()

        assert "error" not in result
        assert "risks" in result
        assert "summary" in result
        assert len(result["risks"]) >= 6

    def test_read_contract_baseline(self):
        """Test reading contract baseline."""
        result = read_contract_baseline()

        assert "error" not in result
        assert result["contract_number"] == "FA8611-21-C-0042"
        assert "contract_type" in result

    def test_read_contract_mods_all(self):
        """Test reading all contract mods."""
        result = read_contract_mods()

        assert "error" not in result
        assert "mods" in result
        assert result["mod_count"] >= 3
        assert result["filter_applied"] is None

    def test_read_contract_mods_filtered(self):
        """Test reading filtered contract mods."""
        result = read_contract_mods("P00027")

        assert "error" not in result
        assert "mods" in result
        assert result["filter_applied"] == "P00027"
        if result["mod_count"] > 0:
            assert result["mods"][0]["mod_number"].upper() == "P00027"

    def test_read_supplier_metrics_all(self):
        """Test reading all supplier metrics."""
        result = read_supplier_metrics()

        assert "error" not in result
        assert "suppliers" in result
        assert result["supplier_count"] >= 3

    def test_read_supplier_metrics_filtered(self):
        """Test reading filtered supplier metrics."""
        result = read_supplier_metrics("Apex")

        assert "error" not in result
        assert result["filter_applied"] == "Apex"
        assert result["supplier_count"] >= 1

    def test_read_quality_escape_data(self):
        """Test reading quality escape data."""
        result = read_quality_escape_data()

        assert "error" not in result
        assert "escape_id" in result
        assert "severity" in result
        assert "units_affected" in result

    def test_read_cdrl_list(self):
        """Test reading CDRL list."""
        result = read_cdrl_list()

        assert "error" not in result
        assert "cdrls" in result
        assert result["cdrl_count"] >= 10


class TestAnalysisTools:
    """Test analysis/computation tools."""

    def test_calculate_eac_cpi_method(self):
        """Test EAC calculation using CPI method."""
        result = calculate_eac("cpi")

        assert "error" not in result
        assert "eac" in result
        assert "method" in result
        assert result["method"] == "cpi"
        assert result["eac"] > 0

    def test_calculate_eac_composite_method(self):
        """Test EAC calculation using SPI*CPI method."""
        result = calculate_eac("composite")

        assert "error" not in result
        assert "eac" in result
        assert result["method"] == "composite"

    def test_calculate_variance_drivers(self):
        """Test variance driver identification."""
        result = calculate_variance_drivers(5.0)

        assert "error" not in result
        assert "drivers" in result
        assert "threshold_percent" in result

    def test_analyze_cpi_trend(self):
        """Test CPI trend analysis."""
        result = analyze_cpi_trend()

        assert "error" not in result
        assert "trend_direction" in result
        assert "current_cpi" in result

    def test_calculate_risk_exposure(self):
        """Test risk exposure calculation."""
        result = calculate_risk_exposure()

        assert "error" not in result
        assert "total_exposure" in result
        assert "risks" in result

    def test_assess_supplier_risk(self):
        """Test supplier risk assessment."""
        result = assess_supplier_risk("Apex Fastener Corp")

        assert "error" not in result
        assert "supplier_name" in result
        assert "risk_level" in result
        assert "factors" in result

    def test_calculate_copq(self):
        """Test COPQ calculation."""
        result = calculate_cost_of_poor_quality("quality_escape")

        assert "error" not in result
        assert "total_copq" in result
        assert "breakdown" in result

    def test_assess_contract_mod_impact(self):
        """Test contract mod impact assessment."""
        result = assess_contract_mod_impact("P00027")

        assert "error" not in result
        assert "mod_number" in result


class TestToolRegistry:
    """Test tool registry functionality."""

    def test_registry_initialization(self):
        """Test registry initializes correctly."""
        registry = ToolRegistry()

        assert len(registry.tool_names) > 0
        assert len(registry.agent_names) == 6

    def test_get_tools_for_pm_agent(self):
        """Test getting tools for PM agent."""
        registry = ToolRegistry()
        tools = registry.get_tools_for_agent("pm_agent")

        assert len(tools) > 0
        tool_names = [t._func.__name__ for t in tools]
        assert "write_leadership_brief" in tool_names

    def test_get_tools_for_unknown_agent(self):
        """Test getting tools for unknown agent returns empty list."""
        registry = ToolRegistry()
        tools = registry.get_tools_for_agent("unknown_agent")

        assert tools == []

    def test_get_all_tools(self):
        """Test getting all tools."""
        registry = ToolRegistry()
        all_tools = registry.get_all_tools()

        # Should have at least 15 tools total
        assert len(all_tools) >= 15

    def test_get_tool_by_name(self):
        """Test getting tool by name."""
        registry = ToolRegistry()
        tool = registry.get_tool_by_name("read_evm_metrics")

        assert tool is not None
        assert tool._func.__name__ == "read_evm_metrics"

    def test_get_tool_by_name_not_found(self):
        """Test getting non-existent tool returns None."""
        registry = ToolRegistry()
        tool = registry.get_tool_by_name("nonexistent_tool")

        assert tool is None

    def test_tools_are_function_tools(self):
        """Test that all tools are FunctionTool instances."""
        from google.adk.tools import FunctionTool

        registry = ToolRegistry()
        all_tools = registry.get_all_tools()

        for tool in all_tools:
            assert isinstance(tool, FunctionTool)
