"""Tests for verifying external assistants are reachable and respond.

Each assistant defined in the project's ``.env`` file is queried with the
question "What is your purpose?" using the ``call_external_assistant``
function from ``src.tools.external_assistant_tool``.  The test asserts that
the call completes successfully and returns a non‑empty response.

The test suite can be executed with ``pytest -s tests/test_assistants.py``.
"""

import os
import pytest

from src.tools.external_assistant_tool import call_external_assistant


def _load_assistant_ids() -> dict:
    """Extract assistant IDs from the environment.

    The project stores the IDs in ``.env`` using the ``*_ASSISTANT_ID``
    variables.  This helper reads the variables directly from the OS
    environment – the test runner should have sourced ``.env`` beforehand.
    """
    ids = {
        "cam": os.getenv("CAM_ASSISTANT_ID"),
        "pm": os.getenv("PM_ASSISTANT_ID"),
        "risk": os.getenv("RISK_ASSISTANT_ID"),
        "rcca": os.getenv("RCCA_ASSISTANT_ID"),
    }
    # Filter out any missing entries so the test suite can still run if a
    # particular assistant is not configured.
    return {k: v for k, v in ids.items() if v}


@pytest.mark.parametrize("assistant_name,assistant_id", _load_assistant_ids().items())
def test_assistant_response(assistant_name: str, assistant_id: str):
    """Ensure the assistant returns a completed status and some text.

    The query is deliberately simple – most assistants implement a generic
    description for the ``What is your purpose?`` prompt.
    """
    result = call_external_assistant(query="What is your purpose?", assistant_id=assistant_id)

    assert result["status"] == "completed", f"{assistant_name} assistant failed: {result.get('error')}"
    response_text = result.get("response", "")
    assert isinstance(response_text, str) and len(response_text.strip()) > 0, f"Empty response from {assistant_name}"
