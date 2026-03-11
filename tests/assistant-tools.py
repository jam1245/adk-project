can you give me some example usage of out of this?  what if i wanted to just print the assistant descriptions and I had the id 

"""
get_assistant_details.py
========================
Functions to retrieve full assistant metadata from the Genesis API.

The /v1/assistants endpoint returns the complete assistant object including:
  - id, name, description, model
  - instructions (full system prompt)
  - tools (file_search, function, etc.)
  - tool_resources (vector store IDs for file_search)
  - metadata (org, defaultSystemPrompt, etc.)
  - temperature, top_p, response_format
  - created_at (Unix timestamp)

IMPORTANT: Same 403 rule applies — assistant endpoints must NOT include
the openai-organization header. Only these three headers are used:
  Authorization, Content-Type, OpenAI-Beta: assistants=v2

SETUP
-----
    export OPENAI_API_KEY="your-genesis-token-here"

USAGE
-----
    python get_assistant_details.py

Or import:
    from get_assistant_details import get_assistant, list_all_assistants
"""

import os
import json
import requests
import urllib3
from datetime import datetime
from typing import Any, Dict, List, Optional

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE_URL = "https://api.ai.us.lmco.com/v1"
ORGANIZATION = "Business-Acumen-Suite"

aif_token = os.getenv("OPENAI_API_KEY")
if not aif_token:
    # Fallback to the hard‑coded token (kept for backward compatibility)
    aif_token = (
        "token"
    )
os.environ["OPENAI_API_KEY"] = aif_token

# =============================================================================
# CORE HELPERS
# =============================================================================

def _assistant_headers(api_key: str) -> Dict[str, str]:
    """
    Returns the correct headers for assistant endpoints.
    openai-organization is intentionally excluded (causes 403 if included).
    """
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "OpenAI-Beta": "assistants=v2",
    }


def _get_api_key(api_key: Optional[str] = None) -> str:
    key = api_key or os.getenv("OPENAI_API_KEY")
    if not key:
        raise ValueError("No API key found. Set OPENAI_API_KEY or pass api_key=")
    return key


def _fmt_timestamp(ts) -> str:
    """Convert Unix timestamp to readable string."""
    try:
        return datetime.utcfromtimestamp(int(ts)).strftime("%Y-%m-%d %H:%M UTC")
    except Exception:
        return str(ts)


# =============================================================================
# FETCH FUNCTIONS
# =============================================================================

def list_all_assistants(api_key: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Fetch all assistants and return as a list of raw assistant dicts.

    Each dict contains the full assistant object from the API.
    """
    key = _get_api_key(api_key)
    url = f"{BASE_URL}/assistants"

    response = requests.get(url, headers=_assistant_headers(key), verify=False)
    response.raise_for_status()

    return response.json().get("data", [])


def get_assistant(
    assistant_id: str,
    api_key: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Fetch a single assistant by ID and return the full raw dict.

    Parameters
    ----------
    assistant_id : str   UUID of the assistant
    api_key      : str   Optional — defaults to OPENAI_API_KEY env var

    Returns
    -------
    dict with all assistant fields
    """
    key = _get_api_key(api_key)
    url = f"{BASE_URL}/assistants/{assistant_id}"

    response = requests.get(url, headers=_assistant_headers(key), verify=False)
    response.raise_for_status()

    return response.json()


# =============================================================================
# DISPLAY FUNCTIONS
# =============================================================================

def print_assistant_detail(assistant: Dict[str, Any]) -> None:
    """Pretty-print every available field from a single assistant object."""

    print("=" * 70)
    print(f"  {assistant.get('name', 'Unnamed Assistant')}")
    print("=" * 70)

    print(f"  ID          : {assistant.get('id', 'N/A')}")
    print(f"  Model       : {assistant.get('model', 'N/A')}")
    print(f"  Created     : {_fmt_timestamp(assistant.get('created_at', ''))}")

    # Description
    desc = assistant.get("description", "")
    print(f"  Description : {desc if desc else '(none)'}")

    # Tools
    tools = assistant.get("tools", [])
    tool_types = [t.get("type", "unknown") for t in tools]
    print(f"  Tools       : {', '.join(tool_types) if tool_types else 'none'}")

    # Tool resources (e.g. vector store IDs for file_search)
    tool_resources = assistant.get("tool_resources", {})
    if tool_resources:
        print(f"  Tool Resources:")
        for resource_type, resource_data in tool_resources.items():
            print(f"    [{resource_type}] {json.dumps(resource_data)}")

    # Metadata (org, defaultSystemPrompt, custom fields)
    metadata = assistant.get("metadata", {})
    if metadata:
        print(f"  Metadata:")
        for k, v in metadata.items():
            print(f"    {k}: {v}")

    # Model parameters
    print(f"  Temperature     : {assistant.get('temperature', 'N/A')}")
    print(f"  Top P           : {assistant.get('top_p', 'N/A')}")
    print(f"  Response Format : {assistant.get('response_format', 'N/A')}")

    # Full instructions (system prompt)
    instructions = assistant.get("instructions", "")
    if instructions:
        print(f"\n  --- INSTRUCTIONS (system prompt) ---")
        print(f"{instructions}")
    else:
        print(f"\n  Instructions: (none)")

    print()


def print_all_assistant_details(api_key: Optional[str] = None) -> None:
    """Fetch and pretty-print full details for every assistant in the org."""
    assistants = list_all_assistants(api_key)
    print(f"\nFound {len(assistants)} assistant(s)\n")
    for asst in assistants:
        print_assistant_detail(asst)


def print_assistant_by_id(
    assistant_id: str,
    api_key: Optional[str] = None,
) -> None:
    """Fetch and pretty-print details for a single assistant by ID."""
    asst = get_assistant(assistant_id, api_key)
    print_assistant_detail(asst)


def get_assistant_summary_table(api_key: Optional[str] = None) -> None:
    """Print a compact summary table of all assistants."""
    assistants = list_all_assistants(api_key)

    print("\n" + "=" * 110)
    print(f"{'#':<3} {'Name':<30} {'Model':<22} {'Tools':<20} {'Created':<20} {'ID'}")
    print("-" * 110)

    for i, a in enumerate(assistants, 1):
        name    = a.get("name", "")[:29]
        model   = a.get("model", "")[:21]
        tools   = ", ".join(t.get("type","") for t in a.get("tools", [])) or "none"
        tools   = tools[:19]
        created = _fmt_timestamp(a.get("created_at", ""))
        aid     = a.get("id", "")
        print(f"{i:<3} {name:<30} {model:<22} {tools:<20} {created:<20} {aid}")

    print("=" * 110)
    print(f"Total: {len(assistants)} assistants\n")


def export_assistants_to_json(
    filepath: str = "assistants_export.json",
    api_key: Optional[str] = None,
) -> None:
    """
    Export all assistant data to a JSON file — useful for auditing,
    diffing changes over time, or feeding to another system.
    """
    assistants = list_all_assistants(api_key)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(assistants, f, indent=2)
    print(f"Exported {len(assistants)} assistants to: {filepath}")


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":

    # 1. Summary table of all assistants
    print("--- SUMMARY TABLE ---")
    get_assistant_summary_table()

    # 2. Full detail for a single assistant by ID
    print("\n--- SINGLE ASSISTANT DETAIL ---")
    print_assistant_by_id("70a49d3b-5cfb-43ef-994e-b558433b483f")  # RIO

    # 3. Full detail dump for ALL assistants (verbose — comment out if noisy)
    # print("\n--- ALL ASSISTANTS FULL DETAIL ---")
    # print_all_assistant_details()

    # 4. Export everything to JSON for auditing / diffing
    # export_assistants_to_json("assistants_export.json")


from get_assistant_details import get_assistant

assistant_id = "70a49d3b-5cfb-43ef-994e-b558433b483f"
assistant = get_assistant(assistant_id)

print(assistant.get("description", "(no description)"))


from get_assistant_details import get_assistant

assistant_id = "70a49d3b-5cfb-43ef-994e-b558433b483f"
assistant = get_assistant(assistant_id)

print(f"Description: {assistant.get('description', '(none)')}")


from get_assistant_details import get_assistant

assistant_id = "70a49d3b-5cfb-43ef-994e-b558433b483f"
assistant = get_assistant(assistant_id)

print(f"Name: {assistant.get('name', 'Unnamed Assistant')}")
print(f"Description: {assistant.get('description', '(none)')}")


def print_assistant_description_by_id(
    assistant_id: str,
    api_key: Optional[str] = None,
) -> None:
    assistant = get_assistant(assistant_id, api_key)
    print(assistant.get("description", "(none)"))


    from get_assistant_details import list_all_assistants

assistants = list_all_assistants()

for a in assistants:
    print(f"{a.get('id')} | {a.get('name')} | {a.get('description', '(none)')}")