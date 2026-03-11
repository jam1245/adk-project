"""Utility script to load environment variables from .env and run the
assistant test suite, capturing the output to ``test_results.txt``.

This script is used by the assistant to automate the verification that all
configured external assistants respond correctly.
"""

import os
import subprocess
import sys

def load_dotenv(path: str = ".env") -> None:
    """Load key‑value pairs from a .env file into ``os.environ``.

    Lines starting with ``#`` or empty lines are ignored.  Only the first ``=``
    in each line is treated as the separator, allowing values to contain ``=``.
    """
    if not os.path.exists(path):
        return
    with open(path, "r", encoding="utf-8") as f:
        for raw_line in f:
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ[key.strip()] = value.strip()


def main() -> None:
    load_dotenv()
    # Run the pytest suite for the assistant test file
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-s", "tests/test_assistants.py"],
        capture_output=True,
        text=True,
    )
    # Write both stdout and stderr to the results file for full visibility
    with open("test_results.txt", "w", encoding="utf-8") as out:
        out.write(result.stdout)
        out.write("\n")
        out.write(result.stderr)


if __name__ == "__main__":
    main()
