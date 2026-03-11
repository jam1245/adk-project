## General code to call assistants in Gen

"""
call_assistant.py
=================
Minimal test function to call a Genesis assistant by organization and assistant ID.

USAGE
-----
    python call_assistant.py

Or import and call directly:
    from call_assistant import call_assistant
    reply = call_assistant(
        assistant_id="70a49d3b-5cfb-43ef-994e-b558433b483f",
        message="What can you help me with?"
    )
    print(reply)

SETUP
-----
    export OPENAI_API_KEY="your-genesis-token-here"
"""

import os
import json
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- Constants ---------------------------------------------------------------

BASE_URL = "https://api.ai.us.lmco.com/v1"
ORGANIZATION = "Business-Acumen-Suite"

aif_token = os.getenv("OPENAI_API_KEY")
if not aif_token:
    # Fallback to the hard‑coded token (kept for backward compatibility)
    aif_token = (
        "token"
    )
os.environ["OPENAI_API_KEY"] = aif_token

#aif_token = 'use-your-genesis-api-token-here'
#os.environ["OPENAI_API_KEY"] = aif_token
aif_token

# Known assistant IDs for quick reference:
# RIO Assistant Test              -> 70a49d3b-5cfb-43ef-994e-b558433b483f
# CAM Assistant                   -> 80a8ae74-5c29-450f-9fa1-f0330b80d8c1
# Prompting Like a Pro Coach      -> 9e6c47f9-7602-4958-ad69-0d3a1bd2d87d
# PMSA Development Plan Assistant -> ebf83141-4d9a-4405-8d67-10cf36fc475f

# -----------------------------------------------------------------------------


def call_assistant(
    assistant_id: str,
    message: str,
    api_key: str = None,
    verbose: bool = True,
) -> str:
    """
    Send a single message to a Genesis assistant and return the full text reply.

    Per Genesis API docs, assistant endpoints require:
      - Authorization: Bearer <token>
      - Content-Type: application/json
      - OpenAI-Beta: assistants=v2
    NOTE: The openai-organization header is intentionally excluded from assistant
    calls — including it causes a 403 Forbidden error.

    Parameters
    ----------
    assistant_id : str   UUID of the assistant (e.g. "70a49d3b-...")
    message      : str   Your message / prompt to the assistant
    api_key      : str   Genesis Bearer token (defaults to OPENAI_API_KEY env var)
    verbose      : bool  If True, prints status and the reply to stdout

    Returns
    -------
    str  The assistant's full text response, or an error message string.
    """
    api_key = api_key or os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("No API key found. Set OPENAI_API_KEY or pass api_key=")

    # Assistant endpoints: NO organization header (causes 403 if included)
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "OpenAI-Beta": "assistants=v2",
    }

    payload = {
        "assistant_id": assistant_id,
        "thread": {
            "messages": [
                {"role": "user", "content": message}
            ]
        },
        "stream": True,
    }

    url = f"{BASE_URL}/threads/runs"

    if verbose:
        print(f"Calling assistant: {assistant_id}")
        print(f"Message: {message}")
        print("-" * 50)

    try:
        response = requests.post(
            url,
            headers=headers,
            json=payload,
            stream=True,
            verify=False,
        )
        response.raise_for_status()

    except requests.exceptions.HTTPError as e:
        error_msg = f"HTTP Error {response.status_code}: {response.text}"
        print(error_msg)
        return error_msg

    # Parse the SSE stream and collect text from thread.message.delta events
    full_reply = []

    for line in response.iter_lines():
        if not line:
            continue

        line = line.decode("utf-8")

        # SSE lines look like:
        #   event:thread.message.delta
        #   data:{"id":"...","object":"thread.message.delta","delta":{"content":[...]}}
        if line.startswith("event:"):
            current_event = line[6:].strip()

        elif line.startswith("data:"):
            data_str = line[5:].strip()
            if data_str == "[DONE]":
                break
            try:
                data = json.loads(data_str)
            except json.JSONDecodeError:
                continue

            # Extract text chunks from message delta events
            if data.get("object") == "thread.message.delta":
                for item in data.get("delta", {}).get("content", []):
                    if item.get("type") == "text":
                        chunk = item["text"]["value"]
                        full_reply.append(chunk)
                        if verbose:
                            print(chunk, end="", flush=True)

    if verbose:
        print()  # newline after streamed output
        print("-" * 50)

    result = "".join(full_reply)
    return result


# -----------------------------------------------------------------------------
# Quick test — edit ASSISTANT_ID and MESSAGE to try different assistants
# -----------------------------------------------------------------------------

if __name__ == "__main__":

    ASSISTANT_ID = "46ae0561-6465-4a66-8afb-df381add40bc"  # RIO Assistant Test
    MESSAGE = "What can you help me with? Give me a brief overview of your purpose."

    reply = call_assistant(
        assistant_id=ASSISTANT_ID,
        message=MESSAGE,
        verbose=True,
    )

    # reply is also returned as a string if you want to use it programmatically
    # print(f"\nCaptured reply ({len(reply)} chars)")