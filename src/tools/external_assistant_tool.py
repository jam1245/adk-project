"""
External Assistant Tool

Bridges ADK's function tool interface to an external Assistants API
(OpenAI-compatible thread/run pattern).  Configured entirely via environment
variables so no credentials live in source code.

See .env.example for the full list of configuration variables.
"""

from __future__ import annotations

import os
import time
from typing import Any, Dict

import requests
import urllib3

# Suppress the InsecureRequestWarning that fires when verify=False
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _get_config() -> Dict[str, Any]:
    """Read assistant configuration from environment variables."""
    ssl_raw = os.getenv("EXT_ASSISTANT_SSL_VERIFY", "false").lower()
    return {
        "api_key":       os.getenv("EXT_ASSISTANT_API_KEY") or os.getenv("OPENAI_API_KEY", ""),
        "api_base":      os.getenv("EXT_ASSISTANT_API_BASE", "").rstrip("/"),
        "org":           os.getenv("EXT_ASSISTANT_ORG", ""),
        "assistant_id":  os.getenv("EXT_ASSISTANT_ID", ""),
        # ssl_verify=True means "do verify"; "false" string disables it
        "ssl_verify":    ssl_raw not in ("false", "0", "no"),
        "poll_interval": float(os.getenv("EXT_ASSISTANT_POLL_INTERVAL", "2")),
        "poll_timeout":  float(os.getenv("EXT_ASSISTANT_POLL_TIMEOUT", "120")),
    }


def _build_headers(cfg: Dict[str, Any]) -> Dict[str, str]:
    """Build the HTTP headers required by the Assistants API."""
    headers = {
        "Authorization": f"Bearer {cfg['api_key']}",
        "Content-Type":  "application/json",
        "OpenAI-Beta":   "assistants=v2",
    }
    if cfg["org"]:
        headers["OpenAI-Organization"] = cfg["org"]
    return headers


# ---------------------------------------------------------------------------
# Public tool function
# ---------------------------------------------------------------------------

def call_external_assistant(query: str) -> dict:
    """Query the external Risk Assistant for expert risk analysis.

    Sends a query to a pre-built assistant hosted on an external
    platform.  The assistant has purpose-built system instructions and a
    vector store for risk management guidance.

    Use this tool whenever the conversation involves:
    - Risk identification or scoring against the 5x5 matrix
    - Issue tracking and escalation criteria
    - Opportunity identification and capture planning
    - Mitigation or contingency plan development
    - Risk-domain questions that go beyond the local data tools

    Recommended workflow:
    1. Call ``read_risk_register`` and other data tools to gather program state.
    2. Summarise the relevant context into a concise ``query`` string.
    3. Call this tool — the assistant will reason over the query and return
       its analysis.
    4. Incorporate the response into your final risk assessment or register update.

    Args:
        query: The risk management question, scenario, or program data to analyse.
               Include relevant context (CPI/SPI values, milestone status, risk IDs,
               supplier concerns) so the assistant can provide a targeted response.

    Returns:
        dict with the following keys:

        On success:
          - ``status``    : "completed"
          - ``response``  : Full text of the assistant's reply
          - ``assistant`` : "external_assistant"
          - ``thread_id`` : Assistants API thread ID (useful for traceability)

        On failure:
          - ``status`` : "error"
          - ``error``  : Human-readable description of what went wrong
    """
    cfg = _get_config()

    if not cfg["api_key"]:
        return {
            "status": "error",
            "error":  (
                "No API key found.  Set EXT_ASSISTANT_API_KEY (or OPENAI_API_KEY) "
                "in your .env file."
            ),
        }

    if not cfg["api_base"]:
        return {
            "status": "error",
            "error":  "No API base URL configured.  Set EXT_ASSISTANT_API_BASE in your .env file.",
        }

    if not cfg["assistant_id"]:
        return {
            "status": "error",
            "error":  "No assistant ID configured.  Set EXT_ASSISTANT_ID in your .env file.",
        }

    headers    = _build_headers(cfg)
    ssl_verify = cfg["ssl_verify"]
    base       = cfg["api_base"]

    try:
        # -- Step 1: Create a thread and start a run in one request ----------
        payload = {
            "assistant_id": cfg["assistant_id"],
            "thread": {
                "messages": [{"role": "user", "content": query}]
            },
        }

        create_resp = requests.post(
            f"{base}/threads/runs",
            headers=headers,
            json=payload,
            verify=ssl_verify,
            timeout=30,
        )
        create_resp.raise_for_status()
        run_obj = create_resp.json()

        thread_id = run_obj.get("thread_id")
        run_id    = run_obj.get("id")

        if not thread_id or not run_id:
            return {
                "status": "error",
                "error":  f"Unexpected create-run response (missing thread_id/id): {run_obj}",
            }

        # -- Step 2: Poll until the run reaches a terminal state -------------
        terminal_states = {"completed", "failed", "cancelled", "expired"}
        deadline        = time.time() + cfg["poll_timeout"]

        while time.time() < deadline:
            poll_resp = requests.get(
                f"{base}/threads/{thread_id}/runs/{run_id}",
                headers=headers,
                verify=ssl_verify,
                timeout=15,
            )
            poll_resp.raise_for_status()
            run_status = poll_resp.json().get("status", "")

            if run_status == "completed":
                break

            if run_status in terminal_states:
                return {
                    "status": "error",
                    "error":  f"Run ended with status '{run_status}': {poll_resp.json()}",
                }

            time.sleep(cfg["poll_interval"])
        else:
            return {
                "status": "error",
                "error":  f"Timed out after {cfg['poll_timeout']}s waiting for run to complete.",
            }

        # -- Step 3: Retrieve the assistant's reply from the thread ----------
        msgs_resp = requests.get(
            f"{base}/threads/{thread_id}/messages",
            headers=headers,
            verify=ssl_verify,
            timeout=15,
        )
        msgs_resp.raise_for_status()
        messages = msgs_resp.json().get("data", [])

        # Messages are returned newest-first; find the first assistant message
        response_text = ""
        for msg in messages:
            if msg.get("role") == "assistant":
                for block in msg.get("content", []):
                    if block.get("type") == "text":
                        response_text = block["text"]["value"]
                        break
            if response_text:
                break

        return {
            "status":    "completed",
            "assistant": "external_assistant",
            "thread_id": thread_id,
            "response":  response_text or "(No response text returned by assistant)",
        }

    except requests.HTTPError as exc:
        body = exc.response.text[:500] if exc.response is not None else "no body"
        return {
            "status": "error",
            "error":  f"HTTP {exc.response.status_code if exc.response is not None else '?'}: {body}",
        }
    except requests.ConnectionError as exc:
        return {"status": "error", "error": f"Connection error: {exc}"}
    except requests.Timeout:
        return {"status": "error", "error": "Request timed out connecting to external assistant API."}
    except Exception as exc:  # noqa: BLE001
        return {"status": "error", "error": f"{type(exc).__name__}: {exc}"}
