"""
External Assistant Tool

Bridges ADK's function tool interface to an external Assistants API
(OpenAI-compatible thread/run pattern).  Configured entirely via environment
variables so no credentials live in source code.

Includes retry logic with exponential backoff for transient failures and
structured logging for debugging.

See .env.example for the full list of configuration variables.
"""

from __future__ import annotations

import logging
import os
import time
from typing import Any, Dict

import requests
import urllib3

# Suppress the InsecureRequestWarning that fires when verify=False
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger("external_assistant")


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _get_config() -> Dict[str, Any]:
    """Read assistant configuration from environment variables."""
    ssl_raw = os.getenv("EXT_ASSISTANT_SSL_VERIFY", "false").lower()
    return {
        # Support both LM_PLATFORM_* (new) and EXT_ASSISTANT_* (legacy) names
        "api_key":       (
            os.getenv("LM_PLATFORM_API_KEY")
            or os.getenv("EXT_ASSISTANT_API_KEY")
            or os.getenv("OPENAI_API_KEY", "")
        ),
        "api_base":      (
            os.getenv("LM_PLATFORM_BASE_URL")
            or os.getenv("EXT_ASSISTANT_API_BASE", "")
        ).rstrip("/"),
        "org":           os.getenv("EXT_ASSISTANT_ORG", ""),
        # ssl_verify=True means "do verify"; "false" string disables it
        "ssl_verify":    ssl_raw not in ("false", "0", "no"),
        "poll_interval": float(os.getenv("EXT_ASSISTANT_POLL_INTERVAL", "2")),
        "poll_timeout":  float(os.getenv("EXT_ASSISTANT_POLL_TIMEOUT", "120")),
        "max_retries":   int(os.getenv("EXT_ASSISTANT_MAX_RETRIES", "2")),
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


def _is_retryable(exc: Exception) -> bool:
    """Return True if the exception is transient and worth retrying."""
    if isinstance(exc, (requests.ConnectionError, requests.Timeout)):
        return True
    if isinstance(exc, requests.HTTPError) and exc.response is not None:
        return exc.response.status_code in (429, 500, 502, 503, 504)
    return False


def _run_single_attempt(query: str, assistant_id: str, cfg: Dict[str, Any]) -> dict:
    """Execute one create-run → poll → retrieve cycle.

    Returns the result dict (success or error).  Raises on retryable errors
    so the caller can decide whether to retry.
    """
    headers    = _build_headers(cfg)
    ssl_verify = cfg["ssl_verify"]
    base       = cfg["api_base"]

    # -- Step 1: Create a thread and start a run in one request ----------------
    payload = {
        "assistant_id": assistant_id,
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

    logger.info("Run created: thread=%s run=%s assistant=%s", thread_id, run_id, assistant_id)

    # -- Step 2: Poll until the run reaches a terminal state -------------------
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
            logger.warning("Run %s ended with status '%s'", run_id, run_status)
            return {
                "status": "error",
                "error":  f"Run ended with status '{run_status}': {poll_resp.json()}",
            }

        time.sleep(cfg["poll_interval"])
    else:
        logger.warning("Run %s timed out after %ss", run_id, cfg["poll_timeout"])
        return {
            "status": "error",
            "error":  f"Timed out after {cfg['poll_timeout']}s waiting for run to complete.",
        }

    # -- Step 3: Retrieve the assistant's reply from the thread ----------------
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


# ---------------------------------------------------------------------------
# Public tool function
# ---------------------------------------------------------------------------

def call_external_assistant(query: str, assistant_id: str) -> dict:
    """Call an external LM platform assistant with a query.

    Sends a query to a pre-built assistant hosted on an external
    platform (OpenAI-compatible Assistants API).  Retries automatically
    on transient failures (timeouts, 5xx, connection errors).

    Args:
        query: The user's question or request to send to the assistant.
               Include relevant context so the assistant can provide a
               targeted response.
        assistant_id: The ID of the specific assistant on the LM platform.

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
    start_time = time.perf_counter()

    # -- Pre-flight checks (not retryable) -------------------------------------
    if not cfg["api_key"]:
        return {
            "status": "error",
            "error":  (
                "No API key found.  Set LM_PLATFORM_API_KEY (or EXT_ASSISTANT_API_KEY) "
                "in your .env file."
            ),
        }

    if not cfg["api_base"]:
        return {
            "status": "error",
            "error":  "No API base URL configured.  Set LM_PLATFORM_BASE_URL in your .env file.",
        }

    if not assistant_id:
        return {
            "status": "error",
            "error":  "No assistant ID provided.",
        }

    logger.info(
        "Calling external assistant: id=%s query_length=%d max_retries=%d",
        assistant_id, len(query), cfg["max_retries"],
    )

    # -- Attempt with retries --------------------------------------------------
    max_retries = cfg["max_retries"]
    last_error  = None

    for attempt in range(1, max_retries + 1):
        try:
            result = _run_single_attempt(query, assistant_id, cfg)
            elapsed_ms = (time.perf_counter() - start_time) * 1000

            if result["status"] == "completed":
                logger.info(
                    "External assistant succeeded: id=%s attempt=%d/%d elapsed=%.0fms response_length=%d",
                    assistant_id, attempt, max_retries, elapsed_ms, len(result.get("response", "")),
                )
            else:
                logger.warning(
                    "External assistant returned error: id=%s attempt=%d/%d elapsed=%.0fms error=%s",
                    assistant_id, attempt, max_retries, elapsed_ms, result.get("error", "unknown"),
                )

            return result

        except Exception as exc:  # noqa: BLE001
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            last_error = exc

            if _is_retryable(exc) and attempt < max_retries:
                backoff = 2 ** (attempt - 1)  # 1s, 2s, 4s ...
                logger.warning(
                    "Retryable error on attempt %d/%d (backoff=%ds): %s: %s",
                    attempt, max_retries, backoff, type(exc).__name__, exc,
                )
                time.sleep(backoff)
                continue

            # Non-retryable or final attempt — return error
            logger.error(
                "External assistant failed: id=%s attempt=%d/%d elapsed=%.0fms error=%s: %s",
                assistant_id, attempt, max_retries, elapsed_ms, type(exc).__name__, exc,
            )

            if isinstance(exc, requests.HTTPError):
                body = exc.response.text[:500] if exc.response is not None else "no body"
                return {
                    "status": "error",
                    "error":  f"HTTP {exc.response.status_code if exc.response is not None else '?'}: {body}",
                }
            if isinstance(exc, requests.ConnectionError):
                return {"status": "error", "error": f"Connection error: {exc}"}
            if isinstance(exc, requests.Timeout):
                return {"status": "error", "error": "Request timed out connecting to external assistant API."}
            return {"status": "error", "error": f"{type(exc).__name__}: {exc}"}

    # Should not reach here, but just in case
    return {"status": "error", "error": f"All {max_retries} attempts failed. Last error: {last_error}"}
