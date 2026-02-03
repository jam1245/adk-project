# Program Execution Workbench

A multi-agent system for defense program management powered by [Google Agent Development Kit (ADK)](https://google.github.io/adk-docs/).

## Overview

The Program Execution Workbench is an AI-powered decision support system that helps program managers, control account managers, and other stakeholders analyze program data, identify issues, and generate actionable recommendations. It uses a team of specialized agents that work together to provide comprehensive analysis.

### Key Features

- **Multi-Agent Architecture**: Six specialist agents (PM, CAM, RCA, Risk, Contracts, S/Q) that analyze problems from different perspectives
- **Workflow Orchestration**: Sequential triage, parallel analysis, iterative refinement, and synthesis phases
- **Contradiction Detection**: Automatic identification and resolution of conflicting assessments
- **Artifact Generation**: Leadership briefs, variance narratives, 8D reports, risk updates, and more
- **Full Observability**: Structured logging, metrics collection, and execution tracing

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Orchestrator                             │
│  ┌──────────┐  ┌──────────────┐  ┌───────────┐  ┌──────────┐   │
│  │  Triage  │→ │   Parallel   │→ │ Refinement│→ │ Synthesis│   │
│  │ Workflow │  │   Analysis   │  │  (Loop)   │  │   (PM)   │   │
│  └──────────┘  └──────────────┘  └───────────┘  └──────────┘   │
│                       ↓                                          │
│        ┌─────────────────────────────────────┐                  │
│        │        Specialist Agents            │                  │
│        │  ┌─────┐ ┌─────┐ ┌──────┐ ┌─────┐  │                  │
│        │  │ CAM │ │ RCA │ │ Risk │ │ S/Q │  │                  │
│        │  └─────┘ └─────┘ └──────┘ └─────┘  │                  │
│        │           ┌───────────┐             │                  │
│        │           │ Contracts │             │                  │
│        │           └───────────┘             │                  │
│        └─────────────────────────────────────┘                  │
└─────────────────────────────────────────────────────────────────┘
```

### Specialist Agents

| Agent | Role | Key Capabilities |
|-------|------|------------------|
| **PM Agent** | Executive Synthesizer | Leadership briefs, What/Why/So What/Now What structure |
| **CAM Agent** | EVM Analyst | CPI/SPI analysis, variance drivers, EAC projections |
| **RCA Agent** | Root Cause Investigator | 5 Whys, Fishbone, 8D problem-solving |
| **Risk Agent** | Risk Manager | 5x5 matrix, risk exposure, mitigation planning |
| **Contracts Agent** | Contract Specialist | FAR/DFARS, mod analysis, compliance |
| **S/Q Agent** | Supplier/Quality Manager | OTDP, DPMO, quality escape response |

## Installation

### Prerequisites

- Python 3.10+
- Anthropic API key (for Claude models)

### Setup

```bash
# Clone the repository
git clone https://github.com/jam1245/adk-project.git
cd adk-project

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template and configure
cp .env.example .env
# Edit .env with your Anthropic API key
```

### Environment Variables

Edit `.env` and set:

```
ANTHROPIC_API_KEY=your-anthropic-api-key-here
LOG_LEVEL=INFO
MAX_REFINEMENT_ITERATIONS=3
```

Get your Anthropic API key at: https://console.anthropic.com/

## Usage

### ADK Web UI (Recommended)

The easiest way to interact with the agents is through Google ADK's built-in Web UI. This provides a browser-based chat interface for testing all agents.

**Start the Web UI:**

```bash
# Navigate to the project directory
cd adk-project

# Start the ADK web server
adk web adk_agents --port 8000
```

**Open in Browser:**

Navigate to http://127.0.0.1:8000

**Using the Web UI:**

1. Select an agent from the dropdown menu at the top
2. Type your message in the chat input
3. Press Enter or click Send to interact with the agent

**Available Agents:**

| Agent | Description |
|-------|-------------|
| `pm_agent` | Program Manager - Executive synthesis and leadership briefs |
| `cam_agent` | Cost Account Manager - EVM analysis, variance drivers, EAC projections |
| `rca_agent` | Root Cause Analysis - 5 Whys, Fishbone, 8D methodology |
| `risk_agent` | Risk Manager - 5x5 matrix, risk exposure calculations |
| `contracts_agent` | Contracts - FAR/DFARS compliance, modification analysis |
| `sq_agent` | Supplier/Quality - OTDP, DPMO, quality escape investigation |
| `orchestrator` | Full Workbench - All 23 tools, complete multi-agent analysis |

**Example Prompts:**

- For `cam_agent`: "What are the current EVM metrics and variance drivers?"
- For `risk_agent`: "Calculate the total risk exposure for the program"
- For `orchestrator`: "Explain why CPI dropped to 0.87 and recommend corrective actions"

**Stopping the Server:**

Press `Ctrl+C` in the terminal running the server.

---

### Running Demo Scenarios (CLI)

The workbench includes three pre-configured demo scenarios:

```bash
# Run all demo scenarios
python demos/demo_runner.py

# Run specific scenario
python demos/demo_runner.py --scenario variance
python demos/demo_runner.py --scenario contract_change
python demos/demo_runner.py --scenario quality_escape

# Save results to outputs directory
python demos/demo_runner.py --save-results
```

### Interactive Mode

```bash
python demos/demo_runner.py --interactive
```

In interactive mode, you can:
- Submit custom requests in natural language
- Run predefined scenarios with `/scenario <name>`
- View execution metrics with `/metrics`
- Get help with `/help`

### Demo Scenarios

#### Scenario 1: Variance Explanation
- **Trigger**: CPI/SPI threshold breach with milestone slip
- **Analysis**: EVM metrics, work package variance drivers, supplier quality
- **Output**: Leadership brief with corrective actions

#### Scenario 2: Contract Change Assessment
- **Trigger**: New CDRL (cybersecurity) added via contract mod
- **Analysis**: Cost/schedule impact, risk implications
- **Output**: Impact assessment with recommendation

#### Scenario 3: Quality Escape Investigation
- **Trigger**: Defective fasteners discovered at customer site
- **Analysis**: Containment, root cause, COPQ, supplier risk
- **Output**: 8D report with recovery plan

## Project Structure

```
adk-project/
├── adk_agents/              # ADK Web UI agent wrappers
│   ├── pm_agent/            # Program Manager agent
│   ├── cam_agent/           # Cost Account Manager agent
│   ├── rca_agent/           # Root Cause Analysis agent
│   ├── risk_agent/          # Risk Manager agent
│   ├── contracts_agent/     # Contracts agent
│   ├── sq_agent/            # Supplier/Quality agent
│   └── orchestrator/        # Full multi-agent orchestrator
├── src/
│   ├── agents/              # Specialist agent implementations
│   │   ├── pm_agent.py
│   │   ├── cam_agent.py
│   │   ├── rca_agent.py
│   │   ├── risk_agent.py
│   │   ├── contracts_agent.py
│   │   └── sq_agent.py
│   ├── workflows/           # Workflow implementations
│   │   ├── triage.py        # Intent classification
│   │   ├── parallel_analysis.py
│   │   ├── refinement.py    # Contradiction resolution
│   │   └── orchestrator.py  # Main coordinator
│   ├── tools/               # Agent tools (23 total)
│   │   ├── data_tools.py    # Data retrieval (9 tools)
│   │   ├── analysis_tools.py # Analysis (8 tools)
│   │   ├── artifact_tools.py # Artifact generation (6 tools)
│   │   └── tool_registry.py
│   ├── state/               # State management
│   │   ├── models.py        # Pydantic models
│   │   └── state_manager.py
│   ├── memory/              # Memory system
│   ├── contradiction/       # Contradiction detection
│   ├── observability/       # Logging, metrics, tracing
│   └── mock_data/           # Demo data
├── tests/                   # Test suite (20 tests)
├── demos/                   # Demo scenarios
├── outputs/                 # Generated artifacts
│   ├── briefs/
│   ├── artifacts/
│   └── traces/
└── logs/                    # Log files
```

## Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src

# Run specific test module
pytest tests/test_agents.py
pytest tests/test_workflows.py
pytest tests/test_tools.py
pytest tests/test_scenarios.py

# Run with verbose output
pytest -v
```

## API Reference

### Creating the Orchestrator

```python
from src.workflows.orchestrator import create_orchestrator

orchestrator = create_orchestrator(
    app_name="my-app",
    max_refinement_iterations=3
)
```

### Running Analysis

```python
import asyncio

async def main():
    orchestrator = create_orchestrator()

    result = await orchestrator.run(
        trigger="Explain why CPI dropped to 0.87",
        user_id="analyst_1",
        context={"program_name": "My Program"}
    )

    print(result["leadership_brief"])
    print(f"Trace ID: {result['trace_id']}")

asyncio.run(main())
```

### Using Individual Agents

```python
from src.agents.cam_agent import create_cam_agent
from src.tools.tool_registry import ToolRegistry

registry = ToolRegistry()
cam = create_cam_agent(registry)

# Use with ADK Runner
from google.adk import Runner
from google.adk.sessions import InMemorySessionService

runner = Runner(
    app_name="cam-analysis",
    agent=cam,
    session_service=InMemorySessionService()
)
```

### Using Tools Directly

```python
from src.tools.data_tools import read_evm_metrics, read_risk_register
from src.tools.analysis_tools import calculate_eac, calculate_risk_exposure

# Read EVM data
evm = read_evm_metrics()
print(f"CPI: {evm['CPI']}, SPI: {evm['SPI']}")

# Calculate EAC
eac_result = calculate_eac(method="cpi")
print(f"EAC: ${eac_result['eac']:,.0f}")

# Assess risk
risk = calculate_risk_exposure()
print(f"Total Exposure: ${risk['total_exposure']:,.0f}")
```

## Configuration

### Adjusting Agent Behavior

Agent system prompts can be customized in the respective agent files under `src/agents/`. Key customization points:

- Risk scoring matrices
- EVM threshold values
- Output format templates
- Domain-specific terminology

### Adding New Tools

1. Create the tool function in the appropriate file (`data_tools.py`, `analysis_tools.py`, or `artifact_tools.py`)
2. Register the tool in `tool_registry.py` under the appropriate agent(s)
3. Add tests in `tests/test_tools.py`

### Adding New Agents

1. Create a new agent file in `src/agents/`
2. Define the system prompt and create function
3. Add to `tool_registry.py` with tool assignments
4. Update `parallel_analysis.py` to include the agent
5. Update `triage.py` intent-to-agent mapping if needed

## Observability

### Logs

Logs are written to `logs/workbench.log` in JSON format:

```json
{
  "timestamp": "2024-10-15T14:30:00Z",
  "level": "INFO",
  "agent_name": "cam_agent",
  "trace_id": "abc123",
  "message": "Tool call completed",
  "extra_data": {"tool": "read_evm_metrics", "latency_ms": 45}
}
```

### Metrics

Access metrics programmatically:

```python
from src.observability.metrics import MetricsCollector

metrics = MetricsCollector()
summary = metrics.get_summary()
metrics.export_to_json("outputs/traces/metrics.json")
```

### Traces

Execution traces are available in the orchestrator result:

```python
result = await orchestrator.run(trigger="...")
print(result["execution_report"])  # Human-readable report
print(result["trace_id"])          # For trace lookup
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Write tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Acknowledgments

- Built with [Google Agent Development Kit (ADK)](https://google.github.io/adk-docs/)
- Designed for defense acquisition program management workflows
- Mock data represents a fictional "Advanced Fighter Program (AFP)"
