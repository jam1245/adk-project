# Streamlit App Build Instructions: Program Execution Workbench
## With Hidden "Behind the Scenes" Tracing Panel

> **Purpose:** These instructions are for building a Streamlit chat application on top of the
> existing multi-agent ADK system. The app targets non-technical program management users (program
> managers, CAMs, leadership) as its primary audience. A secondary audience (~30% of users) may
> optionally enable a tracing sidebar to understand what the AI system is doing behind the scenes.
>
> **Who implements this:** A developer using these instructions should follow them precisely.
> Every design decision, layout choice, component type, and data flow is specified here.

---

## Table of Contents

1. [What You Are Building](#1-what-you-are-building)
2. [How the Underlying Agent System Works](#2-how-the-underlying-agent-system-works)
3. [How ADK Events and Tracing Work](#3-how-adk-events-and-tracing-work)
4. [File Structure to Create](#4-file-structure-to-create)
5. [Dependencies](#5-dependencies)
6. [App Architecture and State Management](#6-app-architecture-and-state-management)
7. [Connecting Streamlit to the ADK Runner](#7-connecting-streamlit-to-the-adk-runner)
8. [Event Collection and Parsing](#8-event-collection-and-parsing)
9. [Main Chat UI Layout](#9-main-chat-ui-layout)
10. [Sidebar: Behind the Scenes Panel](#10-sidebar-behind-the-scenes-panel)
11. [Trace Waterfall Component](#11-trace-waterfall-component)
12. [Agent Journey Component](#12-agent-journey-component)
13. [Tool Call Detail Component](#13-tool-call-detail-component)
14. [Styling and Theming](#14-styling-and-theming)
15. [Full Annotated Code Skeleton](#15-full-annotated-code-skeleton)
16. [Common Pitfalls and How to Avoid Them](#16-common-pitfalls-and-how-to-avoid-them)

---

## 1. What You Are Building

A **Streamlit web application** that wraps the Program Execution Workbench multi-agent system.
The app presents as a simple, clean chat interface. Users type questions and get answers.

**Primary UI (what 100% of users see):**
- A page title and brief description
- A chat history area showing the conversation
- A text input box at the bottom
- A "Send" button

**Secondary UI (what ~30% of users can optionally enable):**
- A sidebar toggle labeled "Show Behind the Scenes"
- When enabled, the sidebar reveals: which agents handled the request, what tools were called,
  how long each step took, and a visual trace of the agent handoff chain

The tracing sidebar is **hidden by default** and must be **explicitly enabled** by the user via
a checkbox in the sidebar. This ensures the interface remains clean for non-technical users
while giving curious users insight into the AI reasoning process.

---

## 2. How the Underlying Agent System Works

Understanding this is critical before you write any code.

### The Agent Hierarchy

```
User Message
     |
     v
orchestrator  (LlmAgent)
     |
     |-- decides which specialist to use
     v
  [one of four sub-agents]
     |
     pm_agent    --> calls external PM Assistant via HTTP
     risk_agent  --> calls external RIO Assistant via HTTP
     rcca_agent  --> calls external RCCA Assistant via HTTP
     cam_agent   --> calls external CAM Assistant via HTTP
     |
     v
  Final Answer returned to user
```

### What Each Agent Does

| Agent | Triggers When User Asks About |
|-------|-------------------------------|
| `pm_agent` | Leadership briefs, schedule status, program health, executive summaries, milestones |
| `risk_agent` | Risks, mitigation plans, risk register, probability/impact, 5x5 risk matrix |
| `rcca_agent` | Root cause analysis, corrective actions, 5 Whys, Fishbone diagrams, 8D process |
| `cam_agent` | EVM metrics, CPI, SPI, cost variance, EAC, budget performance, earned value |

### The Routing Mechanism

The orchestrator is an LLM agent. It reads the user's message, decides which sub-agent is most
relevant, and issues a **transfer signal** (`transfer_to_agent`). The ADK framework then hands
control to that sub-agent. The sub-agent calls an external HTTP API (the LM platform assistant)
and returns the answer.

This entire sequence generates a stream of **Events** -- each event is an immutable record of
one step in the process. Collecting and displaying these events is what the tracing panel shows.

---

## 3. How ADK Events and Tracing Work

This section is the most important for building the tracing panel correctly.

### What is an ADK Event?

Every significant thing that happens in the agent pipeline emits an **Event**. Events are
produced by the ADK `Runner` as an async generator. You iterate through the generator and
collect events as they arrive.

An Event is a Python object with these key attributes:

```python
event.author              # str: who produced this event
                          # Examples: "user", "orchestrator", "cam_agent", "risk_agent"

event.id                  # str: unique ID for this specific event

event.invocation_id       # str: groups ALL events from one user query into one trace
                          # This is your primary trace correlation key

event.timestamp           # float: Unix timestamp when this event was created

event.content             # Content object (or None): the payload of this event
event.content.parts       # list[Part]: the actual data -- text, function call, or function response

event.partial             # bool: True = still streaming, False = this chunk is complete

event.actions             # EventActions object: control signals and side effects
event.actions.transfer_to_agent   # str or None: if set, orchestrator is handing off to this agent
event.actions.state_delta         # dict: changes to session state
event.actions.artifact_delta      # dict: files/artifacts created
event.actions.escalate            # bool: signals the pipeline to stop

# Helper methods on the event object:
event.is_final_response()         # bool: True if this is the final answer to show the user
event.get_function_calls()        # list: tool invocation requests from the LLM
event.get_function_responses()    # list: results returned from tool executions
```

### What is in event.content.parts?

Each `Part` in `event.content.parts` is one of three types:

**Type 1 - Text (the agent is saying something):**
```python
part.text   # str: the text content of this part
# This is either: the agent's intermediate reasoning, or the final answer to the user
```

**Type 2 - Function Call (the agent wants to call a tool):**
```python
part.function_call.name    # str: name of the tool being called
                           # Examples: "call_cam_assistant", "get_program_context"
part.function_call.args    # dict: the arguments passed to the tool
                           # Example: {"query": "What is the CPI for AFP?"}
```

**Type 3 - Function Response (a tool returned a result):**
```python
part.function_response.name      # str: name of the tool that ran
part.function_response.response  # dict: what the tool returned
                                 # Example: {"status": "completed", "response": "CPI is 0.94..."}
```

### The Sequence of Events for a Typical Query

When a user asks "What is the current SPI for the AFP program?", the event stream looks like:

```
Event 1:  author="orchestrator"
          content.parts[0].function_call.name = "transfer_to_agent"  [NOT SHOWN TO USER]
          actions.transfer_to_agent = "cam_agent"
          --> MEANING: Orchestrator decided to route to cam_agent

Event 2:  author="cam_agent"
          content.parts[0].function_call.name = "call_cam_assistant"
          content.parts[0].function_call.args = {"query": "What is the current SPI..."}
          --> MEANING: cam_agent is calling the external EVM assistant

Event 3:  author="cam_agent"
          content.parts[0].function_response.name = "call_cam_assistant"
          content.parts[0].function_response.response = {"status": "completed", "response": "The SPI for AFP..."}
          --> MEANING: The external assistant returned its answer

Event 4:  author="cam_agent"
          content.parts[0].text = "The current SPI for the AFP program is 0.87..."
          event.is_final_response() = True
          --> MEANING: This is the final answer to show the user
```

### Span Types (for the waterfall view)

The project's custom tracer (`src/observability/tracer.py`) records four span types that
mirror the ADK OpenTelemetry standard:

| Span Name | What It Covers |
|-----------|----------------|
| `invocation` | The entire request from user question to final answer |
| `agent_run` | One agent's execution (orchestrator, cam_agent, etc.) |
| `call_llm` | A single call to the language model |
| `execute_tool` | A single tool call (e.g., calling external assistant) |

Each span has: `agent_name`, `operation`, `start_time`, `end_time`, `duration_ms`, `status`
("ok" or "error"), and a `metadata` dict with extra context.

The spans form a **tree**: `invocation` → `agent_run(orchestrator)` → `agent_run(cam_agent)`
→ `execute_tool(call_cam_assistant)`.

---

## 4. File Structure to Create

Create the following new files. Do not modify any existing project files.

```
adk-project/
├── streamlit_app/
│   ├── __init__.py                  # empty file
│   ├── app.py                       # MAIN FILE: the Streamlit application entry point
│   ├── adk_runner.py                # ADK integration: runs agents and collects events
│   ├── event_parser.py              # Converts raw ADK events to displayable data structures
│   ├── components/
│   │   ├── __init__.py              # empty file
│   │   ├── chat_panel.py            # Renders the main chat conversation
│   │   ├── trace_waterfall.py       # Renders the timing waterfall chart
│   │   ├── agent_journey.py         # Renders the agent handoff flow diagram
│   │   └── tool_detail.py           # Renders expandable tool call details
│   └── styles/
│       └── main.css                 # Custom CSS for the app
```

---

## 5. Dependencies

Add these to `requirements.txt` (they supplement the existing requirements, do not replace them):

```
streamlit>=1.35.0
plotly>=5.22.0
pandas>=2.0.0
```

The existing `requirements.txt` already includes `google-adk`, `requests`, `python-dotenv`.
No other new packages are needed.

---

## 6. App Architecture and State Management

Streamlit re-runs the entire script on every user interaction. You must use
`st.session_state` to persist data across re-runs. Here is exactly what to store:

```python
# Initialize all session state at the top of app.py before any rendering
# Use st.session_state.setdefault() or check 'key' in st.session_state

st.session_state["messages"]           # list[dict]: the full conversation history
                                       # Each entry: {"role": "user"|"assistant", "content": str}

st.session_state["trace_records"]      # list[dict]: one dict per query, contains all
                                       # parsed event data for that query's trace
                                       # See Section 8 for the exact schema

st.session_state["session_id"]         # str: the ADK session ID for the current conversation
                                       # Generated once per Streamlit session

st.session_state["user_id"]            # str: a fixed user identifier for the ADK session service
                                       # Use "streamlit_user" as the default value

st.session_state["show_trace"]         # bool: whether the tracing sidebar is currently visible
                                       # Default: False

st.session_state["selected_trace_idx"] # int or None: which query's trace is currently displayed
                                       # in the sidebar (index into trace_records list)
                                       # Default: None (shows most recent trace automatically)
```

### Session Initialization Code (put at top of app.py)

```python
import streamlit as st
import uuid

def init_session_state():
    """Initialize all session state keys with their default values."""
    defaults = {
        "messages": [],
        "trace_records": [],
        "session_id": str(uuid.uuid4()),
        "user_id": "streamlit_user",
        "show_trace": False,
        "selected_trace_idx": None,
    }
    for key, default_value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default_value
```

---

## 7. Connecting Streamlit to the ADK Runner

Create `streamlit_app/adk_runner.py`. This file handles all interaction with the ADK framework.

### Key Concept: Running ADK Synchronously in Streamlit

Streamlit's main thread is synchronous. ADK's `Runner` is async. You must bridge this with
`asyncio.run()`. Do NOT use `asyncio.get_event_loop()` -- it is deprecated and unreliable.

### The ADK Imports You Need

```python
import asyncio
import sys
from pathlib import Path

# Add the project root to sys.path so imports work
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types as genai_types

# Import the root agent (the orchestrator)
from adk_agents.orchestrator.agent import root_agent
```

### The ADK Runner Initialization

The `Runner` and `InMemorySessionService` must be created **once** and cached. Use Streamlit's
`@st.cache_resource` decorator so they survive re-runs without being recreated.

```python
import streamlit as st

@st.cache_resource
def get_adk_runner():
    """Create the ADK Runner and session service once, cache for the lifetime of the app."""
    session_service = InMemorySessionService()
    runner = Runner(
        agent=root_agent,
        app_name="program_execution_workbench",
        session_service=session_service,
    )
    return runner, session_service
```

### Creating a Session

Each user gets their own session. Create it when needed (if it does not exist yet).

```python
def ensure_session_exists(session_service, user_id: str, session_id: str):
    """Create the ADK session if it does not already exist."""
    try:
        session_service.get_session(
            app_name="program_execution_workbench",
            user_id=user_id,
            session_id=session_id,
        )
    except Exception:
        # Session does not exist yet, create it
        session_service.create_session(
            app_name="program_execution_workbench",
            user_id=user_id,
            session_id=session_id,
        )
```

### Running a Query and Collecting Events

This is the core function. It sends the user's message to the agent and collects **all** events.

```python
def run_agent_query(user_message: str, user_id: str, session_id: str) -> list[dict]:
    """
    Send a message to the orchestrator and collect all events.

    Returns a list of raw event dicts. Each dict is a serialized Event
    with enough data to drive the tracing UI.

    This function is SYNCHRONOUS (uses asyncio.run internally) so it can
    be called from Streamlit's main thread without issue.
    """
    runner, session_service = get_adk_runner()
    ensure_session_exists(session_service, user_id, session_id)

    # Wrap the user message in ADK's Content type
    user_content = genai_types.Content(
        role="user",
        parts=[genai_types.Part(text=user_message)]
    )

    async def collect_events():
        raw_events = []
        async for event in runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=user_content,
        ):
            raw_events.append(serialize_event(event))
        return raw_events

    return asyncio.run(collect_events())
```

### Serializing an Event to a Dict

The raw ADK event object cannot be stored in `st.session_state` directly (it contains
non-serializable objects). Convert it to a plain dict immediately after receiving it.

```python
def serialize_event(event) -> dict:
    """
    Convert a raw ADK Event object to a plain dict safe for storage in session_state.

    This extracts every attribute you will need for the tracing UI.
    """
    result = {
        "author": event.author,
        "id": str(event.id) if event.id else None,
        "invocation_id": str(event.invocation_id) if event.invocation_id else None,
        "timestamp": event.timestamp if hasattr(event, "timestamp") else None,
        "is_final_response": event.is_final_response(),
        "partial": event.partial if hasattr(event, "partial") else False,

        # Control signals
        "transfer_to_agent": None,
        "escalate": False,

        # Payload type classification
        "event_type": "unknown",   # "text", "tool_call", "tool_response", "handoff", "other"

        # Text content (populated if event_type is "text")
        "text": None,

        # Tool call content (populated if event_type is "tool_call")
        "tool_call_name": None,
        "tool_call_args": None,

        # Tool response content (populated if event_type is "tool_response")
        "tool_response_name": None,
        "tool_response_result": None,
        "tool_response_status": None,   # "completed" or "error" from the external assistant
    }

    # Extract EventActions signals
    if hasattr(event, "actions") and event.actions:
        result["transfer_to_agent"] = getattr(event.actions, "transfer_to_agent", None)
        result["escalate"] = getattr(event.actions, "escalate", False) or False

    # A transfer_to_agent signal makes this a handoff event
    if result["transfer_to_agent"]:
        result["event_type"] = "handoff"

    # Extract content parts
    if event.content and event.content.parts:
        for part in event.content.parts:
            # Text part
            if hasattr(part, "text") and part.text:
                result["text"] = part.text
                if result["event_type"] == "unknown":
                    result["event_type"] = "text"

            # Function call part (agent wants to invoke a tool)
            elif hasattr(part, "function_call") and part.function_call:
                result["tool_call_name"] = part.function_call.name
                result["tool_call_args"] = dict(part.function_call.args) if part.function_call.args else {}
                result["event_type"] = "tool_call"

            # Function response part (tool result came back)
            elif hasattr(part, "function_response") and part.function_response:
                result["tool_response_name"] = part.function_response.name
                raw_response = part.function_response.response
                if isinstance(raw_response, dict):
                    result["tool_response_status"] = raw_response.get("status", "unknown")
                    result["tool_response_result"] = raw_response.get("response", str(raw_response))
                else:
                    result["tool_response_result"] = str(raw_response)
                result["event_type"] = "tool_response"

    return result
```

---

## 8. Event Collection and Parsing

Create `streamlit_app/event_parser.py`. This transforms the list of raw event dicts (from
`adk_runner.py`) into structured data ready for each UI component.

### The Trace Record Schema

After collecting all events for one query, parse them into a `trace_record` dict with this
exact schema:

```python
trace_record = {
    # The user's original question
    "user_query": str,

    # The final text answer from the agent
    "final_answer": str,

    # Unique ID for this invocation (from event.invocation_id)
    "invocation_id": str,

    # When the query was submitted (ISO format string)
    "submitted_at": str,

    # Total time from query submission to final answer (in seconds, float)
    "total_duration_seconds": float,

    # The agent handoff chain as a list of agent names in order
    # Example: ["orchestrator", "cam_agent"]
    "agent_chain": list[str],

    # Which specialist agent handled this query (the last non-orchestrator agent)
    "specialist_agent": str or None,   # None if no sub-agent was used

    # Friendly display name for the specialist
    # Example: "cam_agent" --> "EVM & Cost Performance"
    "specialist_display_name": str or None,

    # List of tool calls made during this query
    "tool_calls": list[dict],   # See tool_call schema below

    # All raw events (for the detailed event log view)
    "raw_events": list[dict],

    # Summary counts for the sidebar header
    "event_count": int,
    "tool_call_count": int,
    "handoff_occurred": bool,
    "had_error": bool,
}

# Each entry in tool_calls:
tool_call_entry = {
    "tool_name": str,          # e.g., "call_cam_assistant"
    "friendly_name": str,      # e.g., "EVM Analysis Assistant"
    "args": dict,              # what was passed to the tool
    "result": str,             # text result from the tool
    "status": str,             # "completed" or "error"
    "called_by_agent": str,    # which agent made this call
}
```

### The Agent Display Name Mapping

Use this mapping whenever you show an agent name to the user. Non-technical users should never
see technical names like "cam_agent" or "rcca_agent".

```python
AGENT_DISPLAY_NAMES = {
    "orchestrator": "Request Router",
    "pm_agent":     "Program Manager Assistant",
    "risk_agent":   "Risk Management Assistant",
    "rcca_agent":   "Root Cause Analysis Assistant",
    "cam_agent":    "EVM & Cost Performance Assistant",
}

AGENT_ROLE_DESCRIPTIONS = {
    "orchestrator": "Reviewed your question and determined which specialist to consult",
    "pm_agent":     "Analyzed program health, schedule status, and leadership priorities",
    "risk_agent":   "Reviewed the risk register and identified mitigation options",
    "rcca_agent":   "Performed root cause analysis using structured problem-solving methods",
    "cam_agent":    "Analyzed earned value metrics, cost performance, and budget data",
}

TOOL_DISPLAY_NAMES = {
    "call_cam_assistant":    "EVM Analysis Assistant",
    "call_pm_assistant":     "Program Manager Assistant",
    "call_risk_assistant":   "Risk & Opportunity Assistant",
    "call_rcca_assistant":   "Root Cause Analysis Assistant",
    "call_cam_assistant_v2": "EVM Analysis Assistant",
    "call_pm_assistant_v2":  "Program Manager Assistant",
    "call_risk_assistant_v2":"Risk & Opportunity Assistant",
    "call_rcca_assistant_v2":"Root Cause Analysis Assistant",
    "get_program_context":   "Program Data Lookup",
    "format_output":         "Response Formatter",
    "log_agent_action":      "Activity Logger",
}
```

### The parse_events() Function

```python
import time
from datetime import datetime

def parse_events(raw_events: list[dict], user_query: str) -> dict:
    """
    Convert a list of raw event dicts into a structured trace_record.

    Call this after run_agent_query() returns. Pass in the list of dicts
    returned by run_agent_query() and the original user query string.
    """
    trace_record = {
        "user_query": user_query,
        "final_answer": "",
        "invocation_id": None,
        "submitted_at": datetime.now().isoformat(),
        "total_duration_seconds": 0.0,
        "agent_chain": [],
        "specialist_agent": None,
        "specialist_display_name": None,
        "tool_calls": [],
        "raw_events": raw_events,
        "event_count": len(raw_events),
        "tool_call_count": 0,
        "handoff_occurred": False,
        "had_error": False,
    }

    # Track timing
    start_ts = None
    end_ts = None

    # Track agent appearances in order (deduplicated, preserving order)
    seen_agents = []

    for event in raw_events:
        # Capture invocation_id from first event that has one
        if trace_record["invocation_id"] is None and event.get("invocation_id"):
            trace_record["invocation_id"] = event["invocation_id"]

        # Track timing from timestamps
        ts = event.get("timestamp")
        if ts:
            if start_ts is None:
                start_ts = ts
            end_ts = ts

        # Build agent chain (each agent that appears, in order, no duplicates)
        author = event.get("author", "")
        if author and author not in seen_agents and author != "user":
            seen_agents.append(author)

        # Capture the final text answer
        if event.get("is_final_response") and event.get("text"):
            trace_record["final_answer"] = event["text"]

        # Capture handoff events
        if event.get("event_type") == "handoff" and event.get("transfer_to_agent"):
            trace_record["handoff_occurred"] = True

        # Capture tool calls (pair call + response together)
        if event.get("event_type") == "tool_call":
            tool_entry = {
                "tool_name": event["tool_call_name"],
                "friendly_name": TOOL_DISPLAY_NAMES.get(
                    event["tool_call_name"], event["tool_call_name"]
                ),
                "args": event.get("tool_call_args", {}),
                "result": None,
                "status": "pending",
                "called_by_agent": event.get("author", "unknown"),
            }
            trace_record["tool_calls"].append(tool_entry)

        # Match tool responses to their calls
        if event.get("event_type") == "tool_response":
            # Find the most recent tool call with the same name that has no result yet
            for tool_entry in reversed(trace_record["tool_calls"]):
                if (tool_entry["tool_name"] == event.get("tool_response_name")
                        and tool_entry["result"] is None):
                    tool_entry["result"] = event.get("tool_response_result", "")
                    tool_entry["status"] = event.get("tool_response_status", "completed")
                    break

    # Compute derived fields
    trace_record["agent_chain"] = seen_agents
    trace_record["tool_call_count"] = len(trace_record["tool_calls"])

    # Determine specialist agent (last agent in chain that is not orchestrator)
    for agent in reversed(seen_agents):
        if agent != "orchestrator":
            trace_record["specialist_agent"] = agent
            trace_record["specialist_display_name"] = AGENT_DISPLAY_NAMES.get(agent, agent)
            break

    # Compute total duration
    if start_ts is not None and end_ts is not None:
        try:
            trace_record["total_duration_seconds"] = round(end_ts - start_ts, 2)
        except (TypeError, ValueError):
            trace_record["total_duration_seconds"] = 0.0

    # Check for errors
    for tool_entry in trace_record["tool_calls"]:
        if tool_entry["status"] == "error":
            trace_record["had_error"] = True
            break

    return trace_record
```

---

## 9. Main Chat UI Layout

Create `streamlit_app/app.py`. This is the entry point -- run it with `streamlit run streamlit_app/app.py`.

### Page Configuration (must be the FIRST Streamlit call)

```python
st.set_page_config(
    page_title="Program Execution Workbench",
    page_icon="🛡️",
    layout="wide",         # Use wide layout so the sidebar does not crowd the chat
    initial_sidebar_state="collapsed",   # Sidebar hidden by default
)
```

### Main Layout Structure

The app uses Streamlit's two-column or sidebar approach. Use the **sidebar** for tracing
(not a second column), because sidebars can be fully collapsed and hidden.

```
+----------------------------------------------------------+
|  🛡️  Program Execution Workbench                        |
|  Your AI-powered decision support tool for program mgmt  |
+----------------------------------------------------------+
|                                                          |
|  [chat message 1 - user]                                |
|  [chat message 1 - assistant]                           |
|  [chat message 2 - user]                                |
|  [chat message 2 - assistant]                           |
|                                                          |
|  ... (scrollable chat history) ...                       |
|                                                          |
+----------------------------------------------------------+
|  [text input: "Ask about your program..."]    [Send]     |
+----------------------------------------------------------+

SIDEBAR (collapsed by default):
+------------------------+
| ⚙️ Behind the Scenes   |
| [x] Show agent tracing |
|                        |
| -- Agent Journey --    |
| ┌─────────────────┐   |
| │  [query router] │   |
| │       ↓        │   |
| │  [cam agent]   │   |
| └─────────────────┘   |
|                        |
| -- What Happened --    |
| ✓ Question analyzed    |
| ✓ EVM specialist used  |
| ✓ Tool call made       |
|                        |
| -- Timing --           |
| [waterfall bars]       |
+------------------------+
```

### Header Section

```python
def render_header():
    st.title("🛡️ Program Execution Workbench")
    st.caption(
        "Your AI-powered assistant for program management. "
        "Ask questions about schedule, cost, risk, or program health."
    )
    st.divider()
```

### Chat History Rendering

Use a container with fixed height to make the chat scrollable. Render messages oldest-first.

```python
def render_chat_history():
    """Render all messages in the conversation history."""
    chat_container = st.container(height=500)

    with chat_container:
        if not st.session_state["messages"]:
            # Show a welcome message when no conversation has started
            st.markdown(
                """
                **Welcome!** I can help you with:
                - 📊 **Schedule & program status** -- "What is the current schedule health?"
                - 💰 **Cost & earned value** -- "What is the CPI for AFP this month?"
                - ⚠️ **Risks & mitigations** -- "What are the top risks to the program?"
                - 🔍 **Root cause analysis** -- "Why did we miss the last milestone?"
                - 📋 **Leadership briefs** -- "Prepare an executive summary for the program review"

                *Type your question below to get started.*
                """
            )
        else:
            for message in st.session_state["messages"]:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])
```

### Input Section

```python
def render_input_section():
    """Render the user input and send button."""
    # st.chat_input creates a pinned text box at the bottom of the page
    user_input = st.chat_input(
        placeholder="Ask about your program... (e.g., 'What is the CPI for AFP?')",
        key="chat_input",
    )
    return user_input
```

### Handling a Submission

```python
def handle_user_submission(user_input: str):
    """Process user input: run the agent, collect events, update state."""
    if not user_input.strip():
        return

    # Add the user message to history immediately
    st.session_state["messages"].append({"role": "user", "content": user_input})

    # Show a spinner while the agent is running
    with st.spinner("Consulting the specialists..."):
        # Import from adk_runner
        from streamlit_app.adk_runner import run_agent_query
        from streamlit_app.event_parser import parse_events

        raw_events = run_agent_query(
            user_message=user_input,
            user_id=st.session_state["user_id"],
            session_id=st.session_state["session_id"],
        )

        trace_record = parse_events(raw_events, user_input)

    # Extract the final answer
    final_answer = trace_record["final_answer"]
    if not final_answer:
        final_answer = "I was unable to get a response. Please try again."

    # Add assistant message to history
    st.session_state["messages"].append({"role": "assistant", "content": final_answer})

    # Save the trace record
    st.session_state["trace_records"].append(trace_record)

    # Auto-select the new trace for the sidebar
    st.session_state["selected_trace_idx"] = len(st.session_state["trace_records"]) - 1

    # Trigger a re-run to refresh the UI
    st.rerun()
```

---

## 10. Sidebar: Behind the Scenes Panel

This is the hidden tracing panel. It is rendered inside `st.sidebar`. The user enables it
with a checkbox. When enabled, the sidebar expands automatically.

### Sidebar Toggle and Header

```python
def render_sidebar():
    """Render the entire sidebar content."""
    with st.sidebar:
        st.markdown("### ⚙️ Behind the Scenes")
        st.caption("See how AI agents are working on your behalf")

        # The key toggle -- default is False (hidden)
        show_trace = st.checkbox(
            "Show agent activity",
            value=st.session_state.get("show_trace", False),
            key="show_trace_checkbox",
            help="Enable this to see which AI agents handled your question and how long each step took.",
        )
        st.session_state["show_trace"] = show_trace

        if not show_trace:
            st.markdown(
                """
                ---
                *Enable "Show agent activity" above to see how your questions
                are being processed by the AI system.*
                """
            )
            return

        # If no queries have been made yet, show a placeholder
        if not st.session_state["trace_records"]:
            st.info("Ask a question in the chat to see agent activity here.")
            return

        # Query selector: allow user to look at previous queries' traces
        render_trace_selector()

        # Get the selected trace record
        idx = st.session_state.get("selected_trace_idx", 0)
        if idx is None or idx >= len(st.session_state["trace_records"]):
            idx = len(st.session_state["trace_records"]) - 1
        trace = st.session_state["trace_records"][idx]

        # Render each section
        render_trace_summary(trace)
        st.divider()
        render_agent_journey(trace)
        st.divider()
        render_tool_calls_section(trace)
        st.divider()
        render_event_log(trace)
```

### Query Selector (allows viewing traces for previous questions)

```python
def render_trace_selector():
    """Dropdown to select which query's trace to display."""
    records = st.session_state["trace_records"]
    if len(records) <= 1:
        return   # Only one query, no need for a selector

    # Build display labels -- truncate long queries
    options = []
    for i, r in enumerate(records):
        query_preview = r["user_query"][:40] + ("..." if len(r["user_query"]) > 40 else "")
        options.append(f"Query {i+1}: {query_preview}")

    selected_label = st.selectbox(
        "View trace for:",
        options=options,
        index=st.session_state.get("selected_trace_idx", len(options) - 1),
        key="trace_selector",
    )
    st.session_state["selected_trace_idx"] = options.index(selected_label)
```

### Trace Summary Block

This is the first section the user sees. Use plain language, not technical terms.

```python
def render_trace_summary(trace: dict):
    """Render a plain-English summary of what happened."""
    st.markdown("#### What Happened")

    # Status indicator
    if trace["had_error"]:
        st.error("⚠️ One or more steps encountered an error")
    else:
        st.success("✅ All steps completed successfully")

    # Key stats in columns
    col1, col2 = st.columns(2)
    with col1:
        duration = trace.get("total_duration_seconds", 0)
        st.metric("Total Time", f"{duration:.1f}s")
    with col2:
        specialist = trace.get("specialist_display_name") or "General Assistant"
        st.metric("Specialist Used", specialist)

    # Plain-English step-by-step summary
    st.markdown("**Steps taken:**")
    steps = []

    steps.append("✅ Your question was received and analyzed")

    if trace["handoff_occurred"] and trace["specialist_agent"]:
        display_name = AGENT_DISPLAY_NAMES.get(trace["specialist_agent"], trace["specialist_agent"])
        role_desc = AGENT_ROLE_DESCRIPTIONS.get(trace["specialist_agent"], "Specialist analyzed your question")
        steps.append(f"✅ **{display_name}** was selected as the right specialist")
        steps.append(f"✅ {role_desc}")

    if trace["tool_calls"]:
        for tool_call in trace["tool_calls"]:
            friendly = tool_call.get("friendly_name", tool_call["tool_name"])
            status_icon = "✅" if tool_call["status"] != "error" else "⚠️"
            steps.append(f"{status_icon} Called **{friendly}** to retrieve data")

    steps.append("✅ Response prepared and returned to you")

    for step in steps:
        st.markdown(f"- {step}")
```

---

## 11. Trace Waterfall Component

The waterfall shows which agents and tools ran, in what order, and how long each took.
Use a horizontal Plotly bar chart where each bar represents one span.

Create `streamlit_app/components/trace_waterfall.py`.

### Building the Waterfall Data

```python
import plotly.graph_objects as go
import streamlit as st

# Color map for agent/operation types
SPAN_COLORS = {
    "orchestrator": "#4B8BBE",    # Blue
    "pm_agent":     "#306998",    # Dark blue
    "risk_agent":   "#E37B40",    # Orange
    "rcca_agent":   "#6B4C9A",    # Purple
    "cam_agent":    "#2E8B57",    # Green
    "tool_call":    "#B8B8B8",    # Gray
    "default":      "#888888",
}

def render_trace_waterfall(trace: dict):
    """
    Render a horizontal bar (Gantt-style) chart showing the timeline of events.

    Each row is one significant step:
    - The orchestrator's routing decision
    - The specialist agent's execution
    - Each tool call made by the specialist

    Bars are proportional to the percentage of total time each step took.
    Actual millisecond durations are shown in hover tooltips.
    """
    st.markdown("#### How Long Each Step Took")

    raw_events = trace.get("raw_events", [])
    if not raw_events:
        st.caption("No timing data available for this query.")
        return

    # Build span entries from the event stream
    # Since we do not have exact per-event durations from ADK events alone,
    # we estimate relative timing by grouping events by author and sequence.
    spans = build_spans_from_events(raw_events, trace)

    if not spans:
        st.caption("Timing details not available.")
        return

    total_duration = trace.get("total_duration_seconds", 1.0) or 1.0

    # Build the Plotly figure
    fig = go.Figure()

    y_labels = []
    for i, span in enumerate(spans):
        agent = span["agent"]
        label = AGENT_DISPLAY_NAMES.get(agent, agent)
        operation_label = span["operation"]
        color = SPAN_COLORS.get(agent, SPAN_COLORS["default"])

        # Convert durations to percentage of total for x-axis sizing
        start_pct = (span["start_offset"] / total_duration) * 100
        duration_pct = max((span["duration"] / total_duration) * 100, 2.0)  # min 2% for visibility

        fig.add_trace(go.Bar(
            name=label,
            x=[duration_pct],
            y=[f"{label}: {operation_label}"],
            orientation="h",
            base=start_pct,
            marker_color=color,
            hovertemplate=(
                f"<b>{label}</b><br>"
                f"Step: {operation_label}<br>"
                f"Duration: {span['duration_ms']:.0f}ms<br>"
                "<extra></extra>"
            ),
            showlegend=False,
        ))

    fig.update_layout(
        barmode="overlay",
        xaxis=dict(
            title="Timeline (% of total time)",
            range=[0, 105],
            ticksuffix="%",
        ),
        yaxis=dict(autorange="reversed"),
        height=max(150, len(spans) * 45),
        margin=dict(l=10, r=10, t=10, b=30),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(size=11),
    )

    st.plotly_chart(fig, use_container_width=True)
    st.caption(f"Total time: {total_duration:.1f}s")
```

### Building Spans from Events

Since ADK events include timestamps but not durations, synthesize spans by tracking when
each agent first appears and when its last event occurs.

```python
def build_spans_from_events(raw_events: list[dict], trace: dict) -> list[dict]:
    """
    Synthesize timing spans from the event stream.

    Groups events by author and computes start offset + duration for each agent segment.
    Also adds individual tool call spans.
    """
    spans = []

    # Get the first timestamp as the zero point
    first_ts = None
    for ev in raw_events:
        ts = ev.get("timestamp")
        if ts and first_ts is None:
            first_ts = ts
            break

    if first_ts is None:
        return spans

    # Group events by author into time windows
    agent_windows = {}   # agent_name -> {"start": float, "end": float}
    for ev in raw_events:
        author = ev.get("author", "")
        ts = ev.get("timestamp")
        if not author or not ts or author == "user":
            continue
        offset = ts - first_ts
        if author not in agent_windows:
            agent_windows[author] = {"start": offset, "end": offset}
        else:
            agent_windows[author]["end"] = max(agent_windows[author]["end"], offset)

    # Convert to span entries in the order agents first appeared
    seen_order = []
    for ev in raw_events:
        author = ev.get("author", "")
        if author and author != "user" and author not in seen_order:
            seen_order.append(author)

    for agent in seen_order:
        window = agent_windows.get(agent)
        if not window:
            continue
        duration = max(window["end"] - window["start"], 0.05)  # minimum 50ms for visibility
        spans.append({
            "agent": agent,
            "operation": "Processing" if agent == "orchestrator" else "Analysis",
            "start_offset": window["start"],
            "end_offset": window["end"],
            "duration": duration,
            "duration_ms": duration * 1000,
        })

    # Add tool call spans
    for tool_call in trace.get("tool_calls", []):
        called_by = tool_call.get("called_by_agent", "unknown")
        agent_window = agent_windows.get(called_by, {})
        # Place tool call span in the middle of the calling agent's window
        mid = (agent_window.get("start", 0) + agent_window.get("end", 0)) / 2
        spans.append({
            "agent": "tool_call",
            "operation": tool_call.get("friendly_name", tool_call["tool_name"]),
            "start_offset": mid,
            "end_offset": mid + 0.1,
            "duration": 0.1,
            "duration_ms": 100,
        })

    return spans
```

---

## 12. Agent Journey Component

The agent journey shows the handoff chain visually. Use a simple step-flow layout using
Streamlit columns and arrows.

Create `streamlit_app/components/agent_journey.py`.

```python
import streamlit as st

AGENT_ICONS = {
    "orchestrator": "🔀",
    "pm_agent":     "📋",
    "risk_agent":   "⚠️",
    "rcca_agent":   "🔍",
    "cam_agent":    "💰",
}

def render_agent_journey(trace: dict):
    """
    Render the agent handoff chain as a visual flow.

    Shows: [Router] --> [Specialist] with plain-English labels.
    If no handoff occurred (orchestrator answered directly), show just the router.
    """
    st.markdown("#### Which Specialists Were Involved")

    agent_chain = trace.get("agent_chain", [])

    if not agent_chain:
        st.caption("No agent data available.")
        return

    # Build the display chain
    display_items = []
    for agent in agent_chain:
        icon = AGENT_ICONS.get(agent, "🤖")
        name = AGENT_DISPLAY_NAMES.get(agent, agent)
        role = AGENT_ROLE_DESCRIPTIONS.get(agent, "")
        display_items.append({"icon": icon, "name": name, "role": role, "agent_key": agent})

    # Render as a vertical flow with arrows between agents
    for i, item in enumerate(display_items):
        # Agent box
        is_specialist = item["agent_key"] != "orchestrator"
        border_color = "#2E8B57" if is_specialist else "#4B8BBE"

        st.markdown(
            f"""
            <div style="
                border: 2px solid {border_color};
                border-radius: 8px;
                padding: 10px 14px;
                margin: 4px 0;
                background-color: {'#f0fff4' if is_specialist else '#f0f8ff'};
            ">
                <strong>{item['icon']} {item['name']}</strong><br>
                <small style="color: #555;">{item['role']}</small>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Arrow between agents (but not after the last one)
        if i < len(display_items) - 1:
            st.markdown(
                "<div style='text-align:center; font-size:20px; color:#888; margin:2px 0;'>↓</div>",
                unsafe_allow_html=True,
            )

    # Explanatory note for non-technical users
    if len(display_items) > 1:
        specialist = display_items[-1]
        st.caption(
            f"Your question was automatically routed to the "
            f"**{specialist['name']}** based on its content."
        )
    else:
        st.caption("Your question was handled directly by the routing agent.")
```

---

## 13. Tool Call Detail Component

Each tool call gets its own expandable section showing what was asked and what was returned.
This is the most technical section -- write it with plain-English labels.

Create `streamlit_app/components/tool_detail.py`.

```python
import streamlit as st

def render_tool_calls_section(trace: dict):
    """
    Render expandable details for each tool call made during this query.

    Each tool call becomes an st.expander with:
    - The friendly tool name
    - What was asked (the query passed to the tool)
    - What was returned (the result from the tool)
    - Success/failure status
    """
    tool_calls = trace.get("tool_calls", [])
    if not tool_calls:
        st.caption("No external tools were called during this query.")
        return

    st.markdown("#### Data Sources Consulted")
    st.caption("These are the AI assistants and data sources that were queried.")

    for i, tool_call in enumerate(tool_calls):
        friendly_name = tool_call.get("friendly_name", tool_call["tool_name"])
        status = tool_call.get("status", "unknown")
        status_icon = "✅" if status == "completed" else "⚠️"

        with st.expander(f"{status_icon} {friendly_name}", expanded=False):
            # What was asked
            args = tool_call.get("args", {})
            if args:
                query_text = args.get("query", "")
                if query_text:
                    st.markdown("**Question sent to this assistant:**")
                    st.info(query_text)

            # What was returned
            result = tool_call.get("result", "")
            if result:
                st.markdown("**Response received:**")
                # Truncate very long responses in the sidebar -- full response is in chat
                if len(result) > 500:
                    st.text_area(
                        label="",
                        value=result[:500] + "\n\n[... see full response in chat window ...]",
                        height=150,
                        disabled=True,
                        key=f"tool_result_{i}",
                    )
                else:
                    st.text_area(
                        label="",
                        value=result,
                        height=100,
                        disabled=True,
                        key=f"tool_result_{i}",
                    )

            # Technical details (collapsed further)
            with st.expander("Technical details", expanded=False):
                st.markdown(f"- **Internal tool name:** `{tool_call['tool_name']}`")
                st.markdown(f"- **Called by:** `{tool_call.get('called_by_agent', 'unknown')}`")
                st.markdown(f"- **Status:** `{status}`")
                if args:
                    st.markdown("**Full arguments passed:**")
                    st.json(args)
```

### Event Log Section

Below the tool details, show the raw event log for advanced users.

```python
def render_event_log(trace: dict):
    """
    Render a collapsed event log showing every ADK event in sequence.

    This is the most technical section. It is collapsed by default.
    Each event row shows: event type, author, and a brief description.
    """
    raw_events = trace.get("raw_events", [])
    if not raw_events:
        return

    with st.expander(f"📋 Full Event Log ({len(raw_events)} events)", expanded=False):
        st.caption(
            "Every step the AI system took, in order. "
            "This is the complete record of the agent interaction."
        )

        for i, event in enumerate(raw_events):
            author = event.get("author", "unknown")
            event_type = event.get("event_type", "unknown")
            display_author = AGENT_DISPLAY_NAMES.get(author, author)

            # Build a one-line description for each event
            if event_type == "handoff":
                target = event.get("transfer_to_agent", "unknown")
                target_display = AGENT_DISPLAY_NAMES.get(target, target)
                description = f"Routed to **{target_display}**"
                icon = "🔀"
            elif event_type == "tool_call":
                tool = TOOL_DISPLAY_NAMES.get(event.get("tool_call_name", ""), event.get("tool_call_name", ""))
                description = f"Called **{tool}**"
                icon = "🔧"
            elif event_type == "tool_response":
                tool = TOOL_DISPLAY_NAMES.get(event.get("tool_response_name", ""), event.get("tool_response_name", ""))
                status = event.get("tool_response_status", "")
                icon = "✅" if status == "completed" else "⚠️"
                description = f"Received response from **{tool}**"
            elif event_type == "text" and event.get("is_final_response"):
                description = "Prepared final answer"
                icon = "💬"
            elif event_type == "text":
                text_preview = (event.get("text") or "")[:60]
                description = f"Intermediate response: *{text_preview}...*" if text_preview else "Processing"
                icon = "📝"
            else:
                description = f"Internal step ({event_type})"
                icon = "⚙️"

            st.markdown(
                f"**{i+1}.** {icon} `{display_author}` — {description}"
            )
```

---

## 14. Styling and Theming

Create `streamlit_app/styles/main.css`. Inject it using `st.markdown` with `unsafe_allow_html=True`.

```css
/* Inject at the top of app.py with:
   with open("streamlit_app/styles/main.css") as f:
       st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
*/

/* Remove default Streamlit padding for a cleaner look */
.block-container {
    padding-top: 1.5rem;
    padding-bottom: 1rem;
}

/* Chat messages */
[data-testid="stChatMessage"] {
    border-radius: 8px;
    margin-bottom: 8px;
}

/* User messages - right-aligned */
[data-testid="stChatMessage"][data-author="user"] {
    background-color: #e8f4fd;
}

/* Sidebar header */
.sidebar-title {
    font-size: 1.1rem;
    font-weight: 600;
    color: #333;
}

/* Metric cards in the sidebar */
[data-testid="metric-container"] {
    background-color: #f8f9fa;
    border-radius: 6px;
    padding: 8px;
}

/* Plotly chart container */
[data-testid="stPlotlyChart"] {
    border: 1px solid #e0e0e0;
    border-radius: 8px;
    padding: 4px;
}
```

---

## 15. Full Annotated Code Skeleton

Below is the complete `app.py` with all pieces assembled. Use this as the authoritative
reference for the entry point file.

```python
"""
streamlit_app/app.py

Program Execution Workbench - Streamlit Interface

Entry point: streamlit run streamlit_app/app.py

This file orchestrates the full UI:
  1. Page config and CSS injection
  2. Session state initialization
  3. Sidebar (Behind the Scenes tracing panel)
  4. Main chat area header
  5. Chat history display
  6. User input and submission handling
"""

import sys
from pathlib import Path

# Make the project root importable
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import streamlit as st
import uuid
from datetime import datetime

# ============================================================
# 1. PAGE CONFIG (must be the very first Streamlit call)
# ============================================================
st.set_page_config(
    page_title="Program Execution Workbench",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ============================================================
# 2. CSS INJECTION
# ============================================================
css_path = Path(__file__).parent / "styles" / "main.css"
if css_path.exists():
    with open(css_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# ============================================================
# 3. SESSION STATE INITIALIZATION
# ============================================================
def init_session_state():
    defaults = {
        "messages": [],
        "trace_records": [],
        "session_id": str(uuid.uuid4()),
        "user_id": "streamlit_user",
        "show_trace": False,
        "selected_trace_idx": None,
    }
    for key, default_value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default_value

init_session_state()

# ============================================================
# 4. IMPORT APP MODULES (after sys.path is set)
# ============================================================
from streamlit_app.adk_runner import run_agent_query
from streamlit_app.event_parser import (
    parse_events,
    AGENT_DISPLAY_NAMES,
    AGENT_ROLE_DESCRIPTIONS,
    TOOL_DISPLAY_NAMES,
)
from streamlit_app.components.trace_waterfall import render_trace_waterfall
from streamlit_app.components.agent_journey import render_agent_journey
from streamlit_app.components.tool_detail import render_tool_calls_section, render_event_log

# ============================================================
# 5. SIDEBAR RENDERING
# ============================================================
with st.sidebar:
    st.markdown("### ⚙️ Behind the Scenes")
    st.caption("Understand how the AI is working for you")

    show_trace = st.checkbox(
        "Show agent activity",
        value=st.session_state.get("show_trace", False),
        help="See which AI specialists handled your question and how long each step took.",
    )
    st.session_state["show_trace"] = show_trace

    if show_trace and st.session_state["trace_records"]:
        records = st.session_state["trace_records"]

        # Query selector (only if multiple queries)
        if len(records) > 1:
            options = [
                f"Query {i+1}: {r['user_query'][:35]}{'...' if len(r['user_query']) > 35 else ''}"
                for i, r in enumerate(records)
            ]
            default_idx = st.session_state.get("selected_trace_idx") or len(options) - 1
            selected = st.selectbox("View trace for:", options, index=default_idx)
            trace_idx = options.index(selected)
        else:
            trace_idx = 0

        st.session_state["selected_trace_idx"] = trace_idx
        trace = records[trace_idx]

        # Summary section
        st.divider()
        if trace["had_error"]:
            st.error("⚠️ One or more steps had an error")
        else:
            st.success("✅ Completed successfully")

        col1, col2 = st.columns(2)
        with col1:
            dur = trace.get("total_duration_seconds", 0) or 0
            st.metric("Time", f"{dur:.1f}s")
        with col2:
            specialist = trace.get("specialist_display_name") or "General"
            st.metric("Specialist", specialist.split(" ")[0])

        st.markdown("**Steps taken:**")
        steps = ["✅ Question received and analyzed"]
        if trace["handoff_occurred"] and trace.get("specialist_agent"):
            dn = AGENT_DISPLAY_NAMES.get(trace["specialist_agent"], trace["specialist_agent"])
            rd = AGENT_ROLE_DESCRIPTIONS.get(trace["specialist_agent"], "Specialist consulted")
            steps.append(f"✅ **{dn}** selected")
            steps.append(f"✅ {rd}")
        for tc in trace.get("tool_calls", []):
            icon = "✅" if tc["status"] != "error" else "⚠️"
            steps.append(f"{icon} Called **{tc['friendly_name']}**")
        steps.append("✅ Response delivered")
        for step in steps:
            st.markdown(f"- {step}")

        # Agent journey
        st.divider()
        render_agent_journey(trace)

        # Tool details
        st.divider()
        render_tool_calls_section(trace)

        # Trace waterfall (timing)
        st.divider()
        render_trace_waterfall(trace)

        # Event log (most technical, always collapsed)
        st.divider()
        render_event_log(trace)

    elif show_trace:
        st.info("Ask a question in the chat to see agent activity here.")

    else:
        st.markdown(
            "---\n*Enable 'Show agent activity' above to see how your questions are "
            "processed by the AI system.*"
        )

# ============================================================
# 6. MAIN CONTENT AREA
# ============================================================
st.title("🛡️ Program Execution Workbench")
st.caption(
    "Your AI-powered assistant for program management decisions. "
    "Ask about schedule, cost performance, risks, or request a leadership brief."
)
st.divider()

# Chat history container
chat_area = st.container(height=520)
with chat_area:
    if not st.session_state["messages"]:
        st.markdown(
            """
            **Welcome to the Program Execution Workbench.** I can help with:

            | Topic | Example Question |
            |-------|-----------------|
            | 📊 Schedule & Status | "What is the current schedule health for AFP?" |
            | 💰 Cost & EVM | "What is the CPI for the program this month?" |
            | ⚠️ Risk | "What are the top three risks right now?" |
            | 🔍 Root Cause | "Why did we miss the last milestone?" |
            | 📋 Leadership Brief | "Prepare an executive summary for the program review" |

            *Type your question below to get started.*
            """
        )
    else:
        for message in st.session_state["messages"]:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

# ============================================================
# 7. INPUT AND SUBMISSION
# ============================================================
user_input = st.chat_input(
    placeholder="Ask about your program... (e.g., 'What is the current CPI?')"
)

if user_input:
    # Append user message immediately
    st.session_state["messages"].append({"role": "user", "content": user_input})

    with st.spinner("Consulting the specialists..."):
        raw_events = run_agent_query(
            user_message=user_input,
            user_id=st.session_state["user_id"],
            session_id=st.session_state["session_id"],
        )
        trace_record = parse_events(raw_events, user_input)

    final_answer = trace_record["final_answer"] or "I was unable to retrieve a response. Please try again."
    st.session_state["messages"].append({"role": "assistant", "content": final_answer})
    st.session_state["trace_records"].append(trace_record)
    st.session_state["selected_trace_idx"] = len(st.session_state["trace_records"]) - 1

    st.rerun()
```

---

## 16. Common Pitfalls and How to Avoid Them

### Pitfall 1: AsyncIO Event Loop Errors

**Problem:** `asyncio.run()` raises `RuntimeError: This event loop is already running` in
some environments.

**Solution:** Use the `nest_asyncio` approach as a fallback:
```python
try:
    return asyncio.run(collect_events())
except RuntimeError:
    import nest_asyncio
    nest_asyncio.apply()
    loop = asyncio.new_event_loop()
    return loop.run_until_complete(collect_events())
```
Add `nest_asyncio>=1.6.0` to requirements if this fallback is needed.

### Pitfall 2: ADK Session Already Exists Error

**Problem:** On Streamlit hot-reload, the `InMemorySessionService` is re-created (it is
cached), but session IDs may conflict.

**Solution:** Always use a fresh `session_id` per Streamlit session (generated once in
`init_session_state()`). The `@st.cache_resource` ensures the service is only created once
per server process, but each browser session gets its own UUID.

### Pitfall 3: Empty Final Answer

**Problem:** `event.is_final_response()` may return False for all events if the agent returns
only streaming partial responses, leaving `trace_record["final_answer"]` empty.

**Solution:** After collecting all events, fall back to the last text event from any non-user,
non-orchestrator author:
```python
# In parse_events(), after the main loop:
if not trace_record["final_answer"]:
    # Fall back to last text event from any specialist agent
    for event in reversed(raw_events):
        if event.get("event_type") == "text" and event.get("text"):
            if event.get("author") not in ("user", "orchestrator"):
                trace_record["final_answer"] = event["text"]
                break
    # Last resort: any text event
    if not trace_record["final_answer"]:
        for event in reversed(raw_events):
            if event.get("event_type") == "text" and event.get("text"):
                trace_record["final_answer"] = event["text"]
                break
```

### Pitfall 4: Showing Technical Names to Non-Technical Users

**Problem:** Agent names like `cam_agent`, `rcca_agent` or tool names like
`call_cam_assistant_v2` are meaningless to program managers.

**Solution:** Always pass agent names and tool names through `AGENT_DISPLAY_NAMES` and
`TOOL_DISPLAY_NAMES` dictionaries before displaying them. Never render raw internal names
in the main chat area or in the "Steps taken" summary. Only show raw names inside
"Technical details" expanders within the event log.

### Pitfall 5: Sidebar Not Opening Automatically

**Problem:** When a user first enables tracing, the sidebar may not visually open because
`initial_sidebar_state="collapsed"` was set.

**Solution:** Use `st.set_page_config(initial_sidebar_state="auto")` instead. This
allows Streamlit to manage sidebar open/close state automatically. When content is added
to the sidebar (after enabling the checkbox), Streamlit will show it. Alternatively, add
a note: "Open the sidebar panel to see agent activity (use the arrow at the top left)."

### Pitfall 6: Large Tool Responses Overflowing the Sidebar

**Problem:** External assistant responses can be several hundred words. Displaying the full
response in the sidebar makes it unreadably long.

**Solution:** Truncate at 500 characters in the sidebar's tool detail expander, and add a
note directing the user to the main chat window for the full response. The full response is
always visible in the main chat area anyway.

### Pitfall 7: Missing Timestamps on Events

**Problem:** Not all ADK event objects include a `timestamp` attribute in all versions.

**Solution:** Always use `getattr(event, "timestamp", None)` instead of `event.timestamp`.
In `serialize_event()`, handle `None` timestamps gracefully. The timing calculations in
`parse_events()` and `build_spans_from_events()` must handle `None` start/end times and
default to `0.0` rather than raising exceptions.

### Pitfall 8: Import Errors When Running Streamlit

**Problem:** Streamlit runs from a different working directory than expected, causing
`ModuleNotFoundError` for `adk_agents`, `src`, etc.

**Solution:** At the top of `app.py` and `adk_runner.py`, add:
```python
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent  # points to adk-project/
sys.path.insert(0, str(project_root))
```
This ensures all project imports resolve correctly regardless of where `streamlit run` is
invoked from.

---

## Running the App

```bash
# From the project root directory:
streamlit run streamlit_app/app.py
```

The app opens at `http://localhost:8501`.

To enable tracing:
1. Click the `>` arrow at the top-left of the screen to open the sidebar
2. Check "Show agent activity"
3. Ask a question -- the trace panel populates automatically

---

*End of build instructions.*
