"""
Placeholder Tools

Generic utility tools available to all sub-agents.
Replace with real implementations as platform integrations mature.
"""


def get_program_context() -> dict:
    """Returns basic program context and metadata."""
    return {
        "program": "AFP",
        "status": "active",
        "phase": "execution",
        "note": "Placeholder -- connect to real data source later"
    }


def format_output(content: str) -> str:
    """Formats the agent response for clean delivery."""
    return content.strip()


def log_agent_action(agent_name: str, action: str) -> str:
    """Logs an agent action for observability."""
    print(f"[{agent_name}] {action}")
    return f"Logged: {action}"
