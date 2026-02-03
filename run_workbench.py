#!/usr/bin/env python3
"""
Simple launcher for the Program Execution Workbench.
Double-click this file or run: python run_workbench.py
"""

import subprocess
import sys
from pathlib import Path

def main():
    project_root = Path(__file__).parent
    demo_runner = project_root / "demos" / "demo_runner.py"

    # Run interactive mode
    subprocess.run([sys.executable, str(demo_runner), "--interactive"])

if __name__ == "__main__":
    main()
