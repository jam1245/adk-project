# Program Execution Workbench

A multi-agent AI system for program management built on [Google Agent Development Kit (ADK)](https://google.github.io/adk-docs/).

## Overview

The Program Execution Workbench is an AI-powered decision support system for program managers, control account managers, and program leadership. It uses a two-tier orchestrator + sub-agent architecture: an orchestrator routes requests to the most relevant specialist sub-agent, which calls a dedicated external assistant on your internal LM platform for expert analysis.

## Architecture

```
orchestrator  (LlmAgent -- routes only, never answers directly)
  sub_agents:
    pm_agent    --> PM Assistant    (LM Platform)
    risk_agent  --> RIO Assistant   (LM Platform)
    rcca_agent  --> RCCA Assistant  (LM Platform)
    cam_agent   --> CAM Assistant   (LM Platform)
```

## Agents

| Agent | Role | External Assistant |
|-------|------|--------------------|
| **orchestrator** | Routes requests to the right specialist -- never answers directly | -- |
| **pm_agent** | Leadership briefs, exec summaries, schedule status, program health | PM Assistant |
| **risk_agent** | Risk identification, 5x5 matrix, mitigation, risk register (RIO) | RIO Assistant |
| **rcca_agent** | Root cause analysis, corrective actions, 5 Whys, Fishbone, 8D | RCCA Assistant |
| **cam_agent** | EVM metrics, CPI/SPI, cost variance, EAC projections | CAM Assistant |

## Installation

### Prerequisites

- Python 3.10+
- LLM provider API key (Anthropic, OpenAI, or another provider as configured via `.env`)
- Internal LM platform access (base URL + API key + four assistant IDs)

### Setup

```bash
git clone https://github.com/jam1245/adk-project.git
cd adk-project
python -m venv venv
# Windows: venv\Scripts\activate  |  macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Fill in .env with your keys and assistant IDs
```

### Environment Variables

Minimum required in `.env`:

```bash
| `PROVIDER_API_KEY`=your-llm-provider-api-key

LM_PLATFORM_BASE_URL=https://your-platform/v1
LM_PLATFORM_API_KEY=your-bearer-token

PM_ASSISTANT_ID=your-pm-assistant-id
RISK_ASSISTANT_ID=your-rio-assistant-id
RCCA_ASSISTANT_ID=your-rcca-assistant-id
CAM_ASSISTANT_ID=your-cam-assistant-id
```

See `.env.example` for the full reference including SSL, polling, and legacy fallback vars.

## Usage

### ADK Web UI

```bash
adk web adk_agents --port 8000
```

Open http://127.0.0.1:8000 . Select an agent from the dropdown and start chatting.

**Example prompts:**

- Generate a leadership brief on the current program health
- What are the top risks and their mitigation status?
- Explain why CPI dropped and what corrective actions are needed
- Run a 5 Whys on the wing assembly cost overrun
- What is the current EAC and how does it compare to the BAC?

### Demo Scenarios (CLI)

```bash
python demos/demo_runner.py --scenario variance
python demos/demo_runner.py --scenario contract_change
python demos/demo_runner.py --scenario quality_escape
python demos/demo_runner.py --save-results
```

## Project Structure

```
adk-project/
|-- adk_agents/                        # ADK Web UI entry points
|   |-- orchestrator/agent.py          # LlmAgent, sub_agents=[pm,risk,rcca,cam]
|   |-- pm_agent/agent.py              # Calls PM Assistant
|   |-- risk_agent/agent.py            # Calls RIO Assistant
|   |-- rcca_agent/agent.py            # Calls RCCA Assistant
|   +-- cam_agent/agent.py             # Calls CAM Assistant
|-- src/
|   |-- agents/                        # Legacy implementations (unchanged)
|   |-- tools/
|   |   |-- external_assistant_tool.py # LM platform HTTP bridge
|   |   |-- placeholder_tools.py       # Utility stubs
|   |   |-- data_tools.py              # 10 data read tools
|   |   |-- analysis_tools.py          # 8 compute tools
|   |   |-- artifact_tools.py          # 6 artifact write tools
|   |   +-- tool_registry.py           # Agent-to-tool mapping
|   |-- config/model_config.py
|   |-- state/  memory/  contradiction/  observability/
|   +-- mock_data/                     # Simulated Advanced Fighter Program
|-- demos/
|-- outputs/                           # Generated artifacts (gitignored)
|-- .env.example
|-- pyproject.toml
+-- requirements.txt
```

## How the LM Platform Integration Works

1. Orchestrator receives a request and hands off to the correct sub-agent via ADK `sub_agents` delegation
2. Sub-agent calls its wrapper tool (e.g. `call_pm_assistant(query)`)
3. Wrapper calls `call_external_assistant(query, assistant_id)` with the env-configured assistant ID
4. The function creates an OpenAI-compatible Assistants API thread, polls until complete, and returns the text response
5. Sub-agent returns the response to the user

## Running Tests

```bash
pytest
pytest --cov=src
pytest tests/test_agents.py -v
```

## License

MIT License -- see LICENSE file for details.

## Acknowledgments

- Built with [Google Agent Development Kit (ADK)](https://google.github.io/adk-docs/)
- Designed for acquisition program management workflows
- Mock data represents a fictional Advanced Fighter Program (AFP)
