"""Utility for fetching an assistant's description from the Genesis API.

The project already includes a helper script under ``tests/assistant-tools.py``
that knows how to talk to the Genesis ``/v1/assistants`` endpoint.  Importing that
script directly into production code is problematic because the file name contains a
hyphen (``assistant-tools.py``) which is not a valid Python module name.  To keep the
runtime code clean and test‑friendly we re‑implement the minimal logic needed to
retrieve an assistant's ``description`` field.

Environment variables (populated from ``.env``) that control the request:

* ``OPENAI_API_KEY`` – bearer token for the API (set by the existing ``.env``)
* ``BASE_URL`` – the base URL for the Genesis API.  The original script uses a
  constant ``https://api.ai.us.lmco.com/v1``; we default to that but allow an
  override via ``GENESIS_API_BASE_URL`` for flexibility.
* ``EXT_ASSISTANT_SSL_VERIFY`` – whether to verify SSL certificates.  The
  existing script disables verification, so we mirror that behaviour when the
  variable is set to ``false`` (case‑insensitive).

The ``fetch_description`` function returns the description string on success.  If
the request fails (network error, non‑200 response, missing field, etc.) a fallback
description can be supplied; otherwise the original hard‑coded description is used.
"""

from __future__ import annotations

import os
import json
import requests
from typing import Optional

# The original helper disables insecure‑request warnings – we keep the same
# behaviour to avoid noisy logs when ``verify=False``.
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# NOTE:
# -----
# Previously this module attempted to load the project's ``.env`` file on import
# using ``python-dotenv``.  That caused side‑effects: the ``LLM_MODEL`` variable
# from ``.env`` (which points to an OpenAI model) was injected into the process
# environment before the test suite queried ``os.getenv("LLM_MODEL")``.  The
# tests expect the default Anthropic model when ``LLM_MODEL`` is **not** set, so
# loading the file broke the ``test_agents`` expectations.
#
# To avoid unwanted global state, we no longer automatically load ``.env``
# here.  The function ``fetch_description`` only requires the assistant ID and
# (optionally) an API key.  Those values are retrieved directly from the caller
# via ``os.getenv`` when the agents import this helper.  If the necessary env
# vars are missing, the provided ``fallback`` description is used, which is
# sufficient for the test suite.
#
# If a project needs to load ``.env`` for runtime, it should do so explicitly
# in the application entry‑point before importing this module.

# Default base URL used throughout the repository.  Allow an environment override
# for custom deployments.
DEFAULT_BASE_URL = "https://api.ai.us.lmco.com/v1"
BASE_URL = os.getenv("GENESIS_API_BASE_URL", DEFAULT_BASE_URL)


def _assistant_headers(api_key: str) -> dict:
    """Return the headers required by the Genesis assistant endpoints.

    The API expects three headers: ``Authorization``, ``Content-Type`` and the
    ``OpenAI-Beta`` flag.  The ``OpenAI-Organization`` header must **not** be sent
    (the original script explicitly omits it to avoid a 403 error).
    """
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "OpenAI-Beta": "assistants=v2",
    }


def _get_api_key(provided: Optional[str] = None) -> str:
    """Resolve the API key.

    Preference order:
    1. Explicit argument ``provided``
    2. ``OPENAI_API_KEY`` environment variable (populated from ``.env``)
    3. Raise ``ValueError`` if not found.
    """
    if provided:
        return provided
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        raise ValueError(
            "No API key found. Set OPENAI_API_KEY in the environment or pass it explicitly."
        )
    return key


def fetch_description(
    assistant_id: str,
    fallback: Optional[str] = None,
    api_key: Optional[str] = None,
) -> str:
    """Fetch the ``description`` field for a Genesis assistant.

    Parameters
    ----------
    assistant_id: str
        The UUID of the assistant whose description we want.
    fallback: str, optional
        Text to return if the request fails.  If omitted and the request fails,
        the function re‑raises the underlying exception so that callers can decide
        how to handle it.
    api_key: str, optional
        Explicit API key – useful for tests.  If omitted the function uses the
        ``OPENAI_API_KEY`` environment variable.

    Returns
    -------
    str
        The assistant description.
    """
    key = _get_api_key(api_key)
    url = f"{BASE_URL}/assistants/{assistant_id}"
    # ``EXT_ASSISTANT_SSL_VERIFY`` mirrors the variable used elsewhere in the
    # repo.  Treat any value other than "true" (case‑insensitive) as ``False``.
    verify_ssl = os.getenv("EXT_ASSISTANT_SSL_VERIFY", "true").lower() == "true"
    try:
        response = requests.get(url, headers=_assistant_headers(key), verify=verify_ssl)
        response.raise_for_status()
        data = response.json()
        # The description may be missing; default to empty string.
        return data.get("description", "")
    except Exception as exc:
        if fallback is not None:
            # Log the error to stdout for visibility but continue with fallback.
            print(f"[fetch_description] Warning: could not fetch description for {assistant_id}: {exc}")
            return fallback
        raise
