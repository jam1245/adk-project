#!/usr/bin/env python3
"""
Demo runner for the Program Execution Workbench.

Provides a command-line interface to run demo scenarios and interact
with the multi-agent system.

Usage:
    # Run all demo scenarios
    python demos/demo_runner.py

    # Run specific scenario
    python demos/demo_runner.py --scenario variance
    python demos/demo_runner.py --scenario contract_change
    python demos/demo_runner.py --scenario quality_escape

    # Interactive mode
    python demos/demo_runner.py --interactive
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.workflows.orchestrator import create_orchestrator
from src.observability.logger import get_logger
from src.observability.metrics import MetricsCollector

# Import scenarios
from demos.scenario_1_variance import (
    run_scenario as run_variance_scenario,
    validate_outputs as validate_variance,
    SCENARIO_TITLE as VARIANCE_TITLE,
)
from demos.scenario_2_contract_change import (
    run_scenario as run_contract_scenario,
    validate_outputs as validate_contract,
    SCENARIO_TITLE as CONTRACT_TITLE,
)
from demos.scenario_3_quality_escape import (
    run_scenario as run_quality_scenario,
    validate_outputs as validate_quality,
    SCENARIO_TITLE as QUALITY_TITLE,
)

logger = get_logger("demo_runner")

# Scenario registry
SCENARIOS = {
    "variance": {
        "title": VARIANCE_TITLE,
        "runner": run_variance_scenario,
        "validator": validate_variance,
    },
    "contract_change": {
        "title": CONTRACT_TITLE,
        "runner": run_contract_scenario,
        "validator": validate_contract,
    },
    "quality_escape": {
        "title": QUALITY_TITLE,
        "runner": run_quality_scenario,
        "validator": validate_quality,
    },
}


def print_banner():
    """Print the demo banner."""
    banner = """
================================================================
        PROGRAM EXECUTION WORKBENCH - DEMO RUNNER

  Multi-Agent System for Defense Program Management
  Powered by Google ADK + Claude
================================================================
"""
    print(banner)


def print_scenario_menu():
    """Print the scenario selection menu."""
    print("\nAvailable Scenarios:")
    print("-" * 40)
    for key, scenario in SCENARIOS.items():
        print(f"  {key:20} - {scenario['title']}")
    print()


async def run_single_scenario(scenario_key: str, orchestrator) -> dict:
    """Run a single scenario.

    Parameters
    ----------
    scenario_key : str
        The scenario identifier.
    orchestrator : WorkbenchOrchestrator
        The orchestrator instance.

    Returns
    -------
    dict
        Scenario results including validation status.
    """
    if scenario_key not in SCENARIOS:
        print(f"Error: Unknown scenario '{scenario_key}'")
        print_scenario_menu()
        return {"error": f"Unknown scenario: {scenario_key}"}

    scenario = SCENARIOS[scenario_key]
    print(f"\n{'#'*60}")
    print(f"# Running: {scenario['title']}")
    print(f"{'#'*60}")

    try:
        result = await scenario["runner"](orchestrator)

        # Validate outputs
        validation = scenario["validator"](result)

        print("\nValidation Results:")
        print("-" * 40)
        all_passed = True
        for check, passed in validation.items():
            status = "PASS" if passed else "FAIL"
            print(f"  {check:40} [{status}]")
            if not passed:
                all_passed = False

        result["validation"] = validation
        result["all_validations_passed"] = all_passed

        return result

    except Exception as e:
        logger.error(f"Scenario '{scenario_key}' failed: {e}")
        print(f"\nError running scenario: {e}")
        return {"error": str(e)}


async def run_all_scenarios(orchestrator) -> dict:
    """Run all demo scenarios.

    Parameters
    ----------
    orchestrator : WorkbenchOrchestrator
        The orchestrator instance.

    Returns
    -------
    dict
        Combined results from all scenarios.
    """
    results = {}
    summary = {
        "total": len(SCENARIOS),
        "passed": 0,
        "failed": 0,
    }

    for scenario_key in SCENARIOS:
        result = await run_single_scenario(scenario_key, orchestrator)
        results[scenario_key] = result

        if result.get("all_validations_passed"):
            summary["passed"] += 1
        else:
            summary["failed"] += 1

    # Print summary
    print("\n" + "="*60)
    print("DEMO SUMMARY")
    print("="*60)
    print(f"Total Scenarios: {summary['total']}")
    print(f"Passed: {summary['passed']}")
    print(f"Failed: {summary['failed']}")
    print()

    return {"results": results, "summary": summary}


async def run_interactive_mode(orchestrator):
    """Run the interactive demo mode.

    Parameters
    ----------
    orchestrator : WorkbenchOrchestrator
        The orchestrator instance.
    """
    print("\n" + "="*60)
    print("INTERACTIVE MODE")
    print("="*60)
    print("""
Commands:
  /help     - Show this help
  /scenario - Run a predefined scenario
  /metrics  - Show execution metrics
  /quit     - Exit interactive mode

Or type your own request and press Enter.
""")

    while True:
        try:
            user_input = input("\n> ").strip()

            if not user_input:
                continue

            if user_input.lower() in ("/quit", "/exit", "/q"):
                print("Exiting interactive mode.")
                break

            if user_input.lower() == "/help":
                print("""
Available Commands:
  /help              - Show this help message
  /scenario <name>   - Run a predefined scenario
                       (variance, contract_change, quality_escape)
  /metrics           - Show current execution metrics
  /clear             - Clear the screen
  /quit              - Exit interactive mode

Custom Requests:
  Type any request in natural language, for example:
  - "Explain why CPI dropped to 0.87 this month"
  - "Assess impact of adding cybersecurity CDRL"
  - "Investigate quality escape from Apex Fastener"
""")
                continue

            if user_input.lower().startswith("/scenario"):
                parts = user_input.split(maxsplit=1)
                if len(parts) < 2:
                    print_scenario_menu()
                else:
                    scenario_key = parts[1].strip()
                    await run_single_scenario(scenario_key, orchestrator)
                continue

            if user_input.lower() == "/metrics":
                metrics = MetricsCollector()
                summary = metrics.get_summary()
                print("\nExecution Metrics:")
                print("-" * 40)
                print(json.dumps(summary, indent=2, default=str))
                continue

            if user_input.lower() == "/clear":
                print("\033[2J\033[H")  # ANSI clear screen
                print_banner()
                continue

            # Process custom request
            print(f"\nProcessing: {user_input[:50]}...")
            result = await orchestrator.run(
                trigger=user_input,
                user_id="interactive_user",
            )

            # Display results
            print("\n" + "-"*40)
            print("RESULT")
            print("-"*40)

            if result.get("leadership_brief"):
                print("\nLeadership Brief:")
                print(result["leadership_brief"][:1000])
                if len(result.get("leadership_brief", "")) > 1000:
                    print("... (truncated)")

            print(f"\nCase Intent: {result.get('case_file', {}).get('intent')}")
            print(f"Agents Engaged: {list(result.get('findings', {}).keys())}")
            print(f"Contradictions: {len(result.get('contradictions', []))}")
            print(f"Trace ID: {result.get('trace_id')}")

        except KeyboardInterrupt:
            print("\n\nInterrupted. Type /quit to exit.")
        except Exception as e:
            print(f"\nError: {e}")
            logger.error(f"Interactive mode error: {e}")


def save_results(results: dict, output_dir: Path):
    """Save results to the outputs directory.

    Parameters
    ----------
    results : dict
        Results to save.
    output_dir : Path
        Directory to save results to.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    filename = output_dir / f"demo_results_{timestamp}.json"

    with open(filename, "w") as f:
        json.dump(results, f, indent=2, default=str)

    print(f"\nResults saved to: {filename}")


async def main():
    """Main entry point for the demo runner."""
    parser = argparse.ArgumentParser(
        description="Program Execution Workbench Demo Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python demos/demo_runner.py                    # Run all scenarios
  python demos/demo_runner.py --scenario variance
  python demos/demo_runner.py --interactive
        """,
    )

    parser.add_argument(
        "--scenario",
        choices=list(SCENARIOS.keys()),
        help="Run a specific scenario",
    )

    parser.add_argument(
        "--interactive", "-i",
        action="store_true",
        help="Run in interactive mode",
    )

    parser.add_argument(
        "--save-results",
        action="store_true",
        help="Save results to outputs directory",
    )

    parser.add_argument(
        "--max-iterations",
        type=int,
        default=3,
        help="Maximum refinement iterations (default: 3)",
    )

    args = parser.parse_args()

    print_banner()

    # Create orchestrator
    orchestrator = create_orchestrator(
        max_refinement_iterations=args.max_iterations
    )

    if args.interactive:
        await run_interactive_mode(orchestrator)
    elif args.scenario:
        result = await run_single_scenario(args.scenario, orchestrator)
        if args.save_results:
            save_results(
                {args.scenario: result},
                PROJECT_ROOT / "outputs" / "traces"
            )
    else:
        # Run all scenarios
        results = await run_all_scenarios(orchestrator)
        if args.save_results:
            save_results(results, PROJECT_ROOT / "outputs" / "traces")


if __name__ == "__main__":
    asyncio.run(main())
