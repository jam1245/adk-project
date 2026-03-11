"""Genesis Assistant Prompt Generator

This script generates random prompts and calls each known Genesis assistant a
user‑specified number of times. It re‑uses the ``call_assistant`` helper from
``tests/call-genesis-assistants-example.py`` so that authentication, request
construction and response handling remain consistent with the existing code.

Usage
-----
```bash
python -m tests.genesis_prompt_generator --iterations 5
```
The above command will invoke each assistant 5 times with a randomly chosen
prompt from a small pool.

The script prints a concise summary for each call – the assistant ID, the
prompt used, and the first 200 characters of the assistant's reply. Errors are
caught and printed without halting the remaining iterations.
"""

#Sys.setenv(OPENAI_API_KEY = aif_token)
#Sys.getenv("OPENAI_API_KEY")

aif_token = os.getenv("OPENAI_API_KEY")
if not aif_token:
    # Fallback to the hard‑coded token (kept for backward compatibility)
    aif_token = (
        "eyJhbGciOiJSUzI1NiIsImtpZCI6InVCWDFsbzJjY2gzbkp5R1A5RTNlY2lhV29mQ2RWcFJacWkyWjZNUG9fdGciLCJ0eXAiOiJKV1QifQ.eyJhdWQiOlsiYWlmLWdlbmFpLWFwaSIsImFpZi1mbWFwaS1jbGllbnQiLCJlby1haWZhY3RvcnktcGxhdGZvcm0iXSwiZXhwIjoxNzg4NjU2Mjg1LCJncm91cHMiOlsidXMvcm1zLmJ1c2luZXNzLWFjdW1lbi1hc3Npc3RhbnQtc3VpdGUiXSwiaWF0IjoxNzcyNzU4Njg1LCJpc3MiOiJodHRwczovL2FwaS5haS51cy5sbWNvLmNvbS9hcGkvdjEvdG9rZW5zIiwic2NvcGUiOiJncm91cDp1cy9ybXMuYnVzaW5lc3MtYWN1bWVuLWFzc2lzdGFudC1zdWl0ZSIsInN1YiI6IkJ1c2luZXNzLUFjdW1lbi1TdWl0ZSIsInVwbiI6ImphbSJ9.Ux19yzy17QMs8aR0W5PrO5fReIsN0GtYoI1YE1KDSyvEeTB06EP9-VBkHEHRdTUXKTPBrWz3CnCvr_-7rTDy_TBQLYm-dGhSdY2t7bctb0wv7XENPcAco8UeVrLonwuMr7r7LU3c3u4wWKiN-hu_o4g0LVh4VCqae9VPk9MYz2nfNJAdw8Kv9mn8xcgbghFDTJU3KHl2-zoT-fYaDzQeg3iDgolI7YzX2XhID_Si2nat5KTmi3X4VggvbVeofato4L8303vI1w4imIIj1tJehYjMmhWj3DrQHo4bOfjlbrULEyOWuSwhe429N6rSAvDZiQfcf8dkPENYP9ghNN1drg"
    )
os.environ["OPENAI_API_KEY"] = aif_token

#aif_token = 'use-your-genesis-api-token-here'
#os.environ["OPENAI_API_KEY"] = aif_token
aif_token


from __future__ import annotations

import argparse
import random
import sys
from typing import List

# Import the shared ``call_assistant`` implementation via the wrapper module.
# The original helper resides in a hyphen‑named file, which cannot be imported
# directly.  The wrapper ``call_genesis_assistants_example_wrapper`` loads the
# function dynamically and provides a clean importable name.
from .call_genesis_assistants_example_wrapper import call_assistant

# ---------------------------------------------------------------------------
# Configuration – known assistant IDs (copied from the comment block in the
# original ``call-genesis-assistants-example.py``)
# ---------------------------------------------------------------------------
ASSISTANT_IDS: List[str] = [
    "70a49d3b-5cfb-43ef-994e-b558433b483f",  # RIO Assistant Test
    "80a8ae74-5c29-450f-9fa1-f0330b80d8c1",  # CAM Assistant
    "9e6c47f9-7602-4958-ad69-0d3a1bd2d87d",  # Prompting Like a Pro Coach
    "ebf83141-4d9a-4405-8d67-10cf36fc475f",  # PMSA Development Plan Assistant
]

# A small pool of example prompts. These are generic enough to be understood by
# any of the assistants while still exercising different capabilities.
PROMPT_POOL: List[str] = [
    "Give me a brief overview of your purpose.",
    "What are the key risks you can identify?",
    "Explain the cost variance for the program.",
    "Summarize the latest contract modification.",
    "Provide a quick status update on the schedule.",
    "What actions should be taken to mitigate the top risk?",
]


def random_prompt() -> str:
    """Return a random prompt from :data:`PROMPT_POOL`."""
    return random.choice(PROMPT_POOL)


def parse_args(argv: List[str] | None = None) -> argparse.Namespace:
    """Parse command‑line arguments.

    Parameters
    ----------
    argv: list of str, optional
        Argument list to parse; defaults to ``sys.argv[1:]``.
    """
    parser = argparse.ArgumentParser(
        description="Iteratively call each Genesis assistant with random prompts."
    )
    parser.add_argument(
        "-n",
        "--iterations",
        type=int,
        default=1,
        help="Number of times to call each assistant (default: 1)",
    )
    parser.add_argument(
        "--api-key",
        dest="api_key",
        type=str,
        default=None,
        help="Genesis API bearer token. If omitted, the script falls back to the OPENAI_API_KEY environment variable (as used by the original helper).",
    )
    return parser.parse_args(argv)


def main() -> None:
    args = parse_args()
    iterations = max(1, args.iterations)

    for assistant_id in ASSISTANT_IDS:
        print(f"\n--- Assistant {assistant_id} ---")
        for i in range(iterations):
            prompt = random_prompt()
            try:
                reply = call_assistant(
                    assistant_id=assistant_id,
                    message=prompt,
                    verbose=False,
                    api_key=args.api_key,
                )
                # Show a concise excerpt of the reply for quick visibility.
                excerpt = reply[:200].replace("\n", " ")
                print(f"[{i + 1}/{iterations}] Prompt: {prompt}")
                print(f"Reply (first 200 chars): {excerpt}\n")
            except Exception as exc:  # pragma: no cover – defensive logging
                print(f"Error calling assistant {assistant_id}: {exc}", file=sys.stderr)


if __name__ == "__main__":
    # When executed via ``python -m tests.genesis_prompt_generator`` the module
    # name resolves to ``tests.genesis_prompt_generator`` and ``__name__`` is set
    # to ``__main__`` – this block runs the script.
    main()

# ---------------------------------------------------------------------------
# Example usage (uncomment to run directly when executing this file):
# ---------------------------------------------------------------------------
# To call each assistant 3 times with random prompts, run:
#
#     python -m tests.genesis_prompt_generator -n 3
#
# This will iterate over the four assistant IDs defined above and print a
# concise excerpt of each response. Adjust ``-n`` to change the iteration count.
