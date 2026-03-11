"""Utility script to run the variance scenario and print the leadership brief.

The script creates a WorkbenchOrchestrator, runs the variance trigger, and prints
the first 500 characters of the generated leadership brief. This is useful for
embedding a concrete example in documentation.
"""

import asyncio
from src.workflows.orchestrator import create_orchestrator


TRIGGER = """VARIANCE REPORT ALERT - October 2024
Program: Advanced Fighter Program (AFP)
THRESHOLD BREACH DETECTED:
- CPI: 0.87
- SPI: 0.88
- CV: -2100000
- SV: -1800000
MILESTONE ALERT:
- \"Wing Assembly Complete\" slipped 30 days"""


async def main() -> None:
    orchestrator = create_orchestrator()
    result = await orchestrator.run(trigger=TRIGGER, user_id="brief_demo")
    brief = result.get("leadership_brief", "")
    # Print a clear delimiter so we can capture the snippet easily.
    print("---BRIEF START---")
    print(brief[:500])
    print("---BRIEF END---")


if __name__ == "__main__":
    asyncio.run(main())
