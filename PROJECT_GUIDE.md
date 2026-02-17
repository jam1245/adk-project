# Program Execution Workbench — Complete Project Guide

> **Purpose of this document:** This is a self-contained reference for an AI assistant operating
> in a secure environment. It contains everything needed to understand, modify, troubleshoot,
> and extend this project — including the full architecture, every file's role, all recent
> changes, and common troubleshooting scenarios. Read this document fully before answering
> questions about this codebase.

---

## Table of Contents

1. [What This Project Is](#1-what-this-project-is)
2. [Recent Changes — LLM Provider Abstraction](#2-recent-changes--llm-provider-abstraction)
3. [Project File Structure](#3-project-file-structure)
4. [How to Run the Project](#4-how-to-run-the-project)
5. [LLM Configuration (Model Switching)](#5-llm-configuration-model-switching)
6. [Architecture Overview](#6-architecture-overview)
7. [Agent System — The 6 Specialist Agents](#7-agent-system--the-6-specialist-agents)
8. [Tool System — All 23 Tools](#8-tool-system--all-23-tools)
9. [Workflow Pipeline](#9-workflow-pipeline)
10. [State Management](#10-state-management)
11. [Contradiction Detection](#11-contradiction-detection)
12. [Observability Stack](#12-observability-stack)
13. [Memory System](#13-memory-system)
14. [Mock Data & Demo Scenarios](#14-mock-data--demo-scenarios)
15. [ADK Web UI — How It Works](#15-adk-web-ui--how-it-works)
16. [Testing](#16-testing)
17. [Dependencies](#17-dependencies)
18. [Troubleshooting Guide](#18-troubleshooting-guide)
19. [Extending the Project](#19-extending-the-project)
20. [Key Patterns & Conventions](#20-key-patterns--conventions)

---

## 1. What This Project Is

This is a **multi-agent AI system** for defense program management analysis, built on
**Google Agent Development Kit (ADK)**. It simulates a "Program Execution Workbench" where
6 specialist AI agents collaborate to analyze earned value metrics, investigate quality
issues, assess risks, interpret contracts, and produce executive leadership briefs.

**Core technology stack:**
- **Python 3.10+** (language)
- **Google ADK >= 1.15.0** (agent framework — provides Agent, Runner, SequentialAgent, ParallelAgent, LoopAgent)
- **LiteLLM >= 1.0.0** (LLM abstraction — routes to Anthropic, OpenAI, or any OpenAI-compatible endpoint)
- **Pydantic v2** (state models and validation)
- **python-dotenv** (environment variable loading from `.env`)

**The project has two entry points:**
1. `adk web adk_agents --port 8000` — launches the ADK Web UI for interactive agent testing
2. `workbench-demo` — runs pre-built demo scenarios via CLI

---

## 2. Recent Changes — LLM Provider Abstraction

### What Changed and Why

Previously, every agent file hardcoded `LiteLlm(model="anthropic/claude-3-haiku-20240307")`.
This made it impossible to switch LLM providers without editing 15+ files.

The refactor introduced a **single shared configuration module** so that switching between
Anthropic, OpenAI, or any internal OpenAI-compatible endpoint requires only changing
environment variables — zero code changes.

### New Files Created

#### `src/config/__init__.py`
Empty package initializer. Exists only to make `src/config/` a Python package.

#### `src/config/model_config.py`
The single source of truth for LLM configuration. Contains one function:

```python
def get_model() -> LiteLlm:
```

This function reads four environment variables:

| Variable | Default | Purpose |
|----------|---------|---------|
| `LLM_MODEL` | `anthropic/claude-3-haiku-20240307` | LiteLLM model string (format: `provider/model-name`) |
| `LLM_API_BASE` | *(not set)* | Custom API base URL for internal/self-hosted endpoints |
| `LLM_API_KEY` | *(not set)* | API key override (if not set, LiteLLM uses provider-specific env vars like `ANTHROPIC_API_KEY` or `OPENAI_API_KEY`) |
| `LLM_SSL_VERIFY` | `true` | Set to `false` to disable SSL verification for corporate endpoints with self-signed certificates |

It returns a `LiteLlm` instance with these parameters passed as kwargs. The kwargs flow
directly through to `litellm.acompletion()` — this is confirmed by reading the ADK source
code where `completion_args.update(self._additional_args)` merges them in.

### Files Modified

Every file that previously imported `LiteLlm` and hardcoded a model string was updated to
import `get_model` from the shared config instead.

**Pattern — before:**
```python
from google.adk.models.lite_llm import LiteLlm
CLAUDE_MODEL = LiteLlm(model="anthropic/claude-3-haiku-20240307")
# ... later in agent creation:
model=CLAUDE_MODEL,
```

**Pattern — after:**
```python
from src.config.model_config import get_model
# ... later in agent creation:
model=get_model(),
```

**Complete list of modified files (15):**

| File | What Changed |
|------|-------------|
| `src/agents/pm_agent.py` | Replaced `CLAUDE_MODEL` with `get_model()` |
| `src/agents/cam_agent.py` | Same |
| `src/agents/rca_agent.py` | Same |
| `src/agents/risk_agent.py` | Same |
| `src/agents/contracts_agent.py` | Same |
| `src/agents/sq_agent.py` | Same |
| `src/workflows/triage.py` | Same |
| `src/workflows/refinement.py` | Same |
| `adk_agents/pm_agent/agent.py` | Same |
| `adk_agents/cam_agent/agent.py` | Same |
| `adk_agents/rca_agent/agent.py` | Same |
| `adk_agents/risk_agent/agent.py` | Same |
| `adk_agents/contracts_agent/agent.py` | Same |
| `adk_agents/sq_agent/agent.py` | Same |
| `adk_agents/orchestrator/agent.py` | Same |
| `tests/test_agents.py` | `EXPECTED_MODEL` now reads from `os.getenv("LLM_MODEL", ...)` |
| `.env.example` | Added `LLM_MODEL`, `LLM_API_BASE`, `LLM_API_KEY`, `LLM_SSL_VERIFY` documentation |
| `requirements.txt` | Added `openai>=1.0.0` (needed by LiteLLM for OpenAI-compatible endpoints) |

### How to Switch Providers

**Anthropic (default — works with no env changes):**
```bash
ANTHROPIC_API_KEY=sk-ant-...
# LLM_MODEL defaults to anthropic/claude-3-haiku-20240307
```

**OpenAI direct:**
```bash
LLM_MODEL=openai/gpt-4o
LLM_API_KEY=sk-...
```

**Internal OpenAI-compatible endpoint (e.g., corporate LLM gateway):**
```bash
LLM_MODEL=openai/llama-3.3-70b-instruct
LLM_API_BASE=https://api.ai.us.lmco.com/v1
LLM_API_KEY=your-internal-api-key
LLM_SSL_VERIFY=false
```

The `openai/` prefix in `LLM_MODEL` tells LiteLLM to use the OpenAI chat completions API
format (`/v1/chat/completions`). The `LLM_API_BASE` redirects the request to your internal
endpoint instead of `api.openai.com`. This works because your internal endpoint implements
the same OpenAI API spec.

---

## 3. Project File Structure

```
adk-project/
├── .env                          # Your actual API keys (git-ignored)
├── .env.example                  # Template with all env vars documented
├── requirements.txt              # Python dependencies
├── pyproject.toml                # Project metadata and build config
├── pytest.ini                    # Test configuration
├── PROJECT_GUIDE.md              # THIS FILE
│
├── src/                          # Core library code
│   ├── __init__.py
│   ├── config/
│   │   ├── __init__.py
│   │   └── model_config.py       # *** SHARED LLM CONFIG — get_model() ***
│   ├── agents/                   # 6 specialist agent definitions
│   │   ├── __init__.py           # Exports all create_*_agent() functions
│   │   ├── pm_agent.py           # Program Manager — executive synthesis
│   │   ├── cam_agent.py          # Control Account Manager — EVM analysis
│   │   ├── rca_agent.py          # Root Cause Analysis — 5 Whys, Fishbone, 8D
│   │   ├── risk_agent.py         # Risk Management — 5x5 matrix
│   │   ├── contracts_agent.py    # Contracts — FAR/DFARS compliance
│   │   └── sq_agent.py           # Supplier/Quality — supplier performance
│   ├── workflows/                # Multi-agent orchestration
│   │   ├── __init__.py
│   │   ├── orchestrator.py       # Main WorkbenchOrchestrator class
│   │   ├── triage.py             # Intent classification (SequentialAgent)
│   │   ├── parallel_analysis.py  # Parallel specialist execution (ParallelAgent)
│   │   └── refinement.py         # Contradiction resolution loop (LoopAgent)
│   ├── tools/                    # 23 tools across 3 categories
│   │   ├── __init__.py
│   │   ├── tool_registry.py      # Central registry + agent-to-tool mapping
│   │   ├── data_tools.py         # 10 read/fetch tools
│   │   ├── analysis_tools.py     # 8 computation/assessment tools
│   │   └── artifact_tools.py     # 6 document generation tools (write to outputs/)
│   ├── state/                    # Pydantic models + versioned state
│   │   ├── __init__.py
│   │   ├── models.py             # All domain models (EVMMetrics, RiskItem, etc.)
│   │   └── state_manager.py      # Versioned snapshot store
│   ├── contradiction/            # Agent disagreement detection
│   │   ├── __init__.py
│   │   └── detector.py           # 7 contradiction detection rules
│   ├── observability/            # Logging, tracing, metrics
│   │   ├── __init__.py
│   │   ├── logger.py             # JSON-structured logging
│   │   ├── tracer.py             # Distributed-style trace correlation
│   │   └── metrics.py            # Singleton metrics collector
│   ├── memory/                   # Pre-seeded program history
│   │   ├── __init__.py
│   │   ├── memory_store.py       # ADK InMemoryMemoryService wrapper (15 facts)
│   │   └── memory_retrieval.py   # TF-IDF keyword search (20 contextual memories)
│   └── mock_data/                # Demo data for the fictional AFP program
│       ├── __init__.py
│       ├── program_data.py       # Program snapshot (name, budget, WBS, personnel)
│       ├── evm_data.py           # EVM metrics + 6-month history
│       ├── ims_data.py           # 18 IMS milestones + critical path
│       ├── risk_data.py          # 25 risks + summary statistics
│       ├── contract_data.py      # CPIF contract baseline + 4 modifications
│       └── supplier_data.py      # 5 suppliers + quality escape data
│
├── adk_agents/                   # ADK Web UI agent wrappers
│   ├── __init__.py
│   ├── pm_agent/
│   │   ├── __init__.py           # from . import agent
│   │   └── agent.py              # Exports root_agent (required by adk web)
│   ├── cam_agent/
│   │   ├── __init__.py
│   │   └── agent.py
│   ├── rca_agent/
│   │   ├── __init__.py
│   │   └── agent.py
│   ├── risk_agent/
│   │   ├── __init__.py
│   │   └── agent.py
│   ├── contracts_agent/
│   │   ├── __init__.py
│   │   └── agent.py
│   ├── sq_agent/
│   │   ├── __init__.py
│   │   └── agent.py
│   └── orchestrator/
│       ├── __init__.py
│       └── agent.py              # Has ALL 23+ tools (full workbench)
│
├── demos/                        # Pre-built demo scenarios
│   ├── __init__.py
│   ├── demo_runner.py            # CLI entry point (workbench-demo command)
│   ├── scenario_1_variance.py    # CPI/SPI variance explanation
│   ├── scenario_2_contract_change.py  # Contract mod impact analysis
│   └── scenario_3_quality_escape.py   # Quality escape investigation
│
├── tests/                        # Test suite (99 tests)
│   ├── test_agents.py            # 20 tests — agent creation, prompts, tools
│   ├── test_tools.py             # ~40 tests — tool functions, registry
│   ├── test_workflows.py         # ~17 tests — triage, parallel, refinement
│   └── test_scenarios.py         # ~22 tests — end-to-end scenario validation
│
└── outputs/                      # Generated artifacts (created at runtime)
    ├── briefs/                   # Leadership briefs
    └── artifacts/                # CAM narratives, 8D reports, risk updates, etc.
```

---

## 4. How to Run the Project

### Prerequisites
```bash
# Python 3.10+ required
python --version

# Install dependencies
pip install -r requirements.txt
```

### Set Up Environment
```bash
# Copy the example and fill in your keys
cp .env.example .env
# Edit .env with your API key and model settings
```

### Launch ADK Web UI (Primary Usage)
```bash
# This launches a web interface at http://localhost:8000
# You can chat with each agent individually or use the orchestrator
adk web adk_agents --port 8000
```

The web UI discovers agents by scanning `adk_agents/*/agent.py` for `root_agent` variables.
You will see 7 agents available:
- pm_agent, cam_agent, rca_agent, risk_agent, contracts_agent, sq_agent, orchestrator

### Run Demo Scenarios
```bash
workbench-demo
# Or directly:
python -m demos.demo_runner
```

### Run Tests
```bash
# All tests
pytest

# Just agent tests
pytest tests/test_agents.py -v

# Just tool tests
pytest tests/test_tools.py -v
```

---

## 5. LLM Configuration (Model Switching)

### How It Works Internally

All agents call `get_model()` from `src/config/model_config.py`. This function:

1. Reads `LLM_MODEL` env var (default: `anthropic/claude-3-haiku-20240307`)
2. Optionally reads `LLM_API_BASE` for custom endpoint URLs
3. Optionally reads `LLM_API_KEY` for API key override
4. Optionally reads `LLM_SSL_VERIFY` to disable SSL verification
5. Returns `LiteLlm(model=model_name, **kwargs)` with only the non-empty kwargs

The `LiteLlm` class (from `google.adk.models.lite_llm`) stores these kwargs in
`self._additional_args` and merges them into every API call via:
```python
completion_args.update(self._additional_args)
```

This means `api_base`, `api_key`, and `ssl_verify` flow directly to `litellm.acompletion()`.

### Model String Format

LiteLLM uses the format `provider/model-name`:

| Provider | Format | Example |
|----------|--------|---------|
| Anthropic | `anthropic/model-name` | `anthropic/claude-3-haiku-20240307` |
| OpenAI | `openai/model-name` | `openai/gpt-4o` |
| OpenAI-compatible | `openai/model-name` + `LLM_API_BASE` | `openai/llama-3.3-70b-instruct` |
| Google | `gemini/model-name` | `gemini/gemini-1.5-pro` |

### Configuration for Internal OpenAI-Compatible Endpoints

If your organization runs an internal LLM gateway that implements the OpenAI
`/v1/chat/completions` API (like vLLM, TGI, LiteLLM proxy, or a custom gateway):

```bash
# In .env:
LLM_MODEL=openai/llama-3.3-70b-instruct    # "openai/" prefix = use OpenAI API format
LLM_API_BASE=https://your-internal-host/v1  # Redirect to your endpoint
LLM_API_KEY=your-token                      # Your auth token
LLM_SSL_VERIFY=false                        # If using self-signed certs
```

The `openai/` prefix does NOT mean "call OpenAI's servers." It tells LiteLLM which API
format to use. The actual destination is controlled by `LLM_API_BASE`.

### API Key Resolution Order

When `LLM_API_KEY` is set, it is passed directly as `api_key` to LiteLLM and takes
precedence over everything else.

When `LLM_API_KEY` is NOT set, LiteLLM falls back to provider-specific env vars:
- Anthropic models: reads `ANTHROPIC_API_KEY`
- OpenAI models: reads `OPENAI_API_KEY`
- Google models: reads `GOOGLE_API_KEY`

### SSL Verification

Corporate endpoints often use self-signed certificates. Setting `LLM_SSL_VERIFY=false`
passes `ssl_verify=False` to LiteLLM. Alternatively, you can install your corporate CA
certificate and set the `SSL_CERT_FILE` or `REQUESTS_CA_BUNDLE` environment variable
to point to it, which avoids disabling verification entirely.

---

## 6. Architecture Overview

```
                         User Request
                              │
                              ▼
                    ┌─────────────────┐
                    │  ADK Web UI     │  (adk web adk_agents --port 8000)
                    │  or CLI Runner  │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │   Orchestrator   │  (src/workflows/orchestrator.py)
                    │                  │  WorkbenchOrchestrator.run()
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
     Phase 1: TRIAGE   Phase 2: ANALYZE  Phase 3: REFINE   Phase 4: SYNTHESIZE
     ┌────────────┐   ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
     │ Classify    │   │ ParallelAgent│  │  LoopAgent   │  │  PM Agent    │
     │ intent via  │   │ runs 2-5     │  │  resolves    │  │  produces    │
     │ keyword     │   │ specialists  │  │  contradictions│ │  leadership  │
     │ matching    │   │ concurrently │  │  (max 3 iter)│  │  brief       │
     └────────────┘   └──────────────┘  └──────────────┘  └──────────────┘
                             │
          ┌──────────┬───────┼───────┬──────────┐
          ▼          ▼       ▼       ▼          ▼
       cam_agent  rca_agent risk  contracts  sq_agent
                            agent   agent
          │          │       │       │          │
          ▼          ▼       ▼       ▼          ▼
       23 Tools (data read, analysis, artifact generation)
          │
          ▼
       Mock Data (src/mock_data/) or real data sources
```

### Data Flow

1. **Triage** classifies the user's request into one of 5 intents and determines which agents are needed
2. **Parallel Analysis** runs the required specialist agents concurrently (excluding PM)
3. **Contradiction Detection** compares findings across agents using 7 rules
4. **Refinement Loop** attempts to resolve detected contradictions (up to 3 iterations)
5. **Synthesis** PM Agent consolidates all findings into a What/Why/So What/Now What brief
6. **State** is versioned at each phase transition for auditability

---

## 7. Agent System — The 6 Specialist Agents

Each agent is defined in two places:
- `src/agents/<name>.py` — the full implementation with detailed system prompt and `create_<name>_agent()` factory function
- `adk_agents/<name>/agent.py` — a thin wrapper that exports `root_agent` for the ADK Web UI

All agents use the same model from `get_model()` (configurable via env vars).

### PM Agent (Program Manager)
- **File:** `src/agents/pm_agent.py`
- **Role:** Executive synthesizer — consolidates specialist findings into leadership communications
- **Framework:** What/Why/So What/Now What structure
- **Risk levels:** LOW, MEDIUM, HIGH, CRITICAL
- **Tools:** 9 total (all 6 artifact writers + read_program_snapshot + read_evm_metrics + calculate_eac)

### CAM Agent (Control Account Manager)
- **File:** `src/agents/cam_agent.py`
- **Role:** EVM expert — analyzes earned value metrics, identifies variance drivers
- **Framework:** Rate/Efficiency/Schedule/Scope variance categories
- **EAC methods:** CPI, SPI*CPI, Management Estimate
- **Tools:** 8 total (read_evm_metrics, read_evm_history, read_ims_milestones, calculate_eac, calculate_variance_drivers, analyze_cpi_trend, write_cam_narrative, write_action_items)

### RCA Agent (Root Cause Analysis)
- **File:** `src/agents/rca_agent.py`
- **Role:** Problem-solving expert using structured methodologies
- **Framework:** 5 Whys, Fishbone (Ishikawa), 8D Problem-Solving
- **Root cause categories:** Design, Manufacturing, Quality, Supply Chain, Human Factors, Management Systems
- **Tools:** 5 total (read_evm_metrics, read_ims_milestones, read_supplier_metrics, read_quality_escape_data, write_eight_d_report)

### Risk Agent
- **File:** `src/agents/risk_agent.py`
- **Role:** Risk identification, assessment, and mitigation planning
- **Framework:** 5x5 probability/impact matrix
- **Score interpretation:** 1-4 Green, 5-9 Yellow, 10-16 Orange, 17-25 Red
- **Risk categories:** Technical, Schedule, Cost, Supply Chain, Requirements, External
- **Tools:** 6 total (read_risk_register, read_evm_metrics, read_supplier_metrics, calculate_risk_exposure, assess_supplier_risk, write_risk_register_update)

### Contracts Agent
- **File:** `src/agents/contracts_agent.py`
- **Role:** Contract interpretation, mod analysis, FAR/DFARS compliance
- **Contract types:** CPIF, CPFF, FFP, T&M, IDIQ
- **Key clauses:** FAR 52.243 (Changes), FAR 52.249 (Termination), DFARS 252.234 (EVMS)
- **Tools:** 5 total (read_contract_baseline, read_contract_mods, read_cdrl_list, assess_contract_mod_impact, write_contract_change_summary)

### S/Q Agent (Supplier/Quality)
- **File:** `src/agents/sq_agent.py`
- **Role:** Supplier performance monitoring and quality escape investigation
- **Metrics:** OTDP (On-Time Delivery), DPMO (Defects Per Million), Quality Rating (1-5)
- **Response protocol:** Contain > Identify > Notify > Investigate > Correct > Prevent > Verify
- **Tools:** 6 total (read_supplier_metrics, read_quality_escape_data, assess_supplier_risk, calculate_cost_of_poor_quality, write_action_items, write_eight_d_report)

---

## 8. Tool System — All 23 Tools

### Tool Registry (`src/tools/tool_registry.py`)

The `ToolRegistry` class manages tool creation and agent assignment:

```python
registry = ToolRegistry()
tools = registry.get_tools_for_agent("cam_agent")  # Returns list of FunctionTool
all_tools = registry.get_all_tools()                 # 23 deduplicated tools
tool = registry.get_tool_by_name("calculate_eac")   # Single tool lookup
```

Each tool function is wrapped exactly once in a Google ADK `FunctionTool` and shared
across agents. The `_AGENT_TOOL_MAP` dict defines which tools each agent can access.

### Data Tools (`src/tools/data_tools.py`) — 10 tools

All read from `src/mock_data/` and return structured dicts. All use `_safe_call()` wrapper
for error handling and structured logging.

| # | Function | Parameters | Returns |
|---|----------|-----------|---------|
| 1 | `read_program_snapshot()` | none | Program metadata, WBS, personnel |
| 2 | `read_evm_metrics()` | none | CPI, SPI, CV, SV, BCWP, BCWS, ACWP, EAC, BAC, work packages |
| 3 | `read_evm_history()` | none | 6-month EVM trending with period summaries |
| 4 | `read_ims_milestones()` | none | 18 milestones, critical path, schedule status |
| 5 | `read_risk_register()` | none | 25 risks + summary (count by level, cost exposure) |
| 6 | `read_contract_baseline()` | none | Contract number, type, CPIF structure, CLINs |
| 7 | `read_contract_mods(mod_number)` | optional mod_number filter | Contract modifications |
| 8 | `read_cdrl_list()` | none | Contract data requirements with status |
| 9 | `read_supplier_metrics(supplier_name)` | optional supplier_name filter | OTDP, DPMO, ratings, CARs |
| 10 | `read_quality_escape_data()` | none | Quality escape details, impact, containment |

### Analysis Tools (`src/tools/analysis_tools.py`) — 8 tools

| # | Function | Parameters | Returns |
|---|----------|-----------|---------|
| 11 | `calculate_eac(method)` | method: "cpi" / "spi_cpi" / "management" | EAC value, method description, VAC, TCPI |
| 12 | `assess_schedule_criticality(milestone_name)` | milestone name (partial match) | Slip days, critical path status, downstream impacts |
| 13 | `calculate_variance_drivers(threshold_percent)` | threshold (default 5.0) | Work packages exceeding threshold, sorted by magnitude |
| 14 | `calculate_risk_exposure()` | none | Risk exposures (prob x cost), top risks, total |
| 15 | `assess_supplier_risk(supplier_name)` | supplier name (partial match) | Risk score (0-100), factors, recommendations |
| 16 | `calculate_cost_of_poor_quality(event_type)` | event_type: "quality_escape" | COPQ breakdown (labor, material, inspection, delay) |
| 17 | `analyze_cpi_trend()` | none | CPI history, trend direction, acceleration, projected CPI |
| 18 | `assess_contract_mod_impact(mod_number)` | mod number (e.g., "P00027") | Cost/schedule impact, CLINs, risks |

### Artifact Tools (`src/tools/artifact_tools.py`) — 6 tools

All write markdown files to `outputs/briefs/` or `outputs/artifacts/` with UTC timestamps.

| # | Function | Key Parameters | Output |
|---|----------|---------------|--------|
| 19 | `write_leadership_brief(...)` | program_name, intent, what/why/so_what/now_what, risk_level | `outputs/briefs/{ts}_leadership_brief.md` |
| 20 | `write_cam_narrative(...)` | wbs_id, wbs_name, variance_explanation, corrective_actions | `outputs/artifacts/{ts}_cam_narrative_{wbs}.md` |
| 21 | `write_risk_register_update(...)` | risk_id, title, probability, impact, mitigation, status | `outputs/artifacts/{ts}_risk_update_{id}.md` |
| 22 | `write_action_items(items)` | JSON string: [{"action", "owner", "due_date", "priority"}] | `outputs/artifacts/{ts}_action_items.md` |
| 23 | `write_eight_d_report(...)` | problem, containment, root_cause, corrective, preventive, verification | `outputs/artifacts/{ts}_eight_d_report.md` |
| 24 | `write_contract_change_summary(...)` | mod_number, description, cost/schedule_impact, obligations | `outputs/artifacts/{ts}_contract_change_{mod}.md` |

### Agent-to-Tool Mapping

```
pm_agent:        write_leadership_brief, write_cam_narrative, write_risk_register_update,
                 write_action_items, write_eight_d_report, write_contract_change_summary,
                 read_program_snapshot, read_evm_metrics, calculate_eac

cam_agent:       read_evm_metrics, read_evm_history, read_ims_milestones, calculate_eac,
                 calculate_variance_drivers, analyze_cpi_trend, write_cam_narrative,
                 write_action_items

rca_agent:       read_evm_metrics, read_ims_milestones, read_supplier_metrics,
                 read_quality_escape_data, write_eight_d_report

risk_agent:      read_risk_register, read_evm_metrics, read_supplier_metrics,
                 calculate_risk_exposure, assess_supplier_risk, write_risk_register_update

contracts_agent: read_contract_baseline, read_contract_mods, read_cdrl_list,
                 assess_contract_mod_impact, write_contract_change_summary

sq_agent:        read_supplier_metrics, read_quality_escape_data, assess_supplier_risk,
                 calculate_cost_of_poor_quality, write_action_items, write_eight_d_report

orchestrator:    ALL tools (23 total, deduplicated)
```

---

## 9. Workflow Pipeline

### Triage (`src/workflows/triage.py`)

**Intent classification** uses keyword matching against 5 intent patterns:

| Intent | Example Keywords |
|--------|-----------------|
| `explain_variance` | variance, cpi, spi, cost variance, earned value, overrun |
| `assess_contract_change` | contract, mod, modification, change order, cdrl |
| `supplier_quality_investigation` | quality, escape, defect, supplier, dpmo, rework |
| `risk_assessment` | risk, threat, probability, mitigation, contingency |
| `schedule_analysis` | schedule, milestone, slip, delay, critical path |

Each intent maps to a set of required agents via `INTENT_AGENT_MAP`:

```python
"explain_variance":              [cam, rca, risk, pm]
"assess_contract_change":        [contracts, cam, risk, pm]
"supplier_quality_investigation": [sq, rca, cam, contracts, risk, pm]
"risk_assessment":               [risk, cam, pm]
"schedule_analysis":             [cam, risk, pm]
```

The `classify_intent()` function returns `(intent, confidence)` where confidence is
normalized based on keyword hit count.

### Parallel Analysis (`src/workflows/parallel_analysis.py`)

Creates a `ParallelAgent` (ADK built-in) that runs the required specialist agents
concurrently. PM Agent is excluded from parallel analysis — it runs in the synthesis phase.

Two factory functions:
- `create_parallel_analysis_workflow(required_agents, registry)` — selective
- `create_full_parallel_workflow(registry)` — all 5 specialists

### Refinement (`src/workflows/refinement.py`)

Creates a `LoopAgent` (ADK built-in) that iteratively resolves contradictions.
The `ContradictionResolver` helper class tracks resolution state across iterations:

- `should_continue(remaining)` — checks iteration count and remaining contradictions
- `record_resolution(id, resolution, confidence)` — logs a resolution
- `get_summary()` — returns iteration stats

Max iterations configurable via `MAX_REFINEMENT_ITERATIONS` env var (default: 3).

### Orchestrator (`src/workflows/orchestrator.py`)

The `WorkbenchOrchestrator` class coordinates the full pipeline:

```python
orchestrator = WorkbenchOrchestrator(app_name="program-execution-workbench")
result = await orchestrator.run(trigger="Explain the CPI drop", user_id="analyst_1")
```

Returns a dict containing:
- `case_file` — the created case file
- `findings` — aggregated findings from all agents
- `contradictions` — detected contradictions and resolutions
- `leadership_brief` — final synthesized brief
- `artifacts` — all generated artifacts
- `trace_id` — execution trace ID for debugging
- `execution_report` — rendered execution report

---

## 10. State Management

### Domain Models (`src/state/models.py`)

All models use Pydantic v2 `BaseModel`. Key models:

**EVMMetrics:** CPI, SPI, CV, SV, BCWP, BCWS, ACWP, EAC, BAC, VAC, TCPI

**IMSMilestone:** name, baseline_date, forecast_date, actual_date, slip_days, status, criticality

**WorkPackage:** wbs_id, name, budget, actual_cost, percent_complete, responsible_cam, status

**RiskItem:** risk_id, title, description, probability (0-1), impact_level (enum), risk_score (auto-computed), mitigation_plan, status, owner, category
- Has a `@model_validator` that auto-computes risk_score from probability * impact weight

**ContractMod:** mod_number, title, description, mod_type (enum), cost_impact, schedule_impact_weeks, new_deliverables, status

**SupplierMetric:** supplier_name, otdp_percent, dpmo, quality_rating, delivery_rating, corrective_actions_open

**Finding:** agent_name, finding_type (observation/analysis/recommendation/action), content, confidence (0-1), evidence_refs, timestamp

**Contradiction:** id (UUID), finding_a, finding_b, description, severity (low/medium/high), resolution, resolved

**AgentOutput:** agent_name, findings[], overall_confidence, execution_time_ms, tool_calls_made, errors[]

**CaseFile:** case_id, intent, trigger_description, program_name, reporting_period, created_at, required_agents, + optional domain data (evm, milestones, work_packages, risks, contract_mods, supplier_metrics)

**WorkbenchState:** case_file, agent_outputs{}, contradictions[], leadership_brief, artifacts{}, status (triaging/analyzing/refining/synthesizing/complete), iteration_count

### State Manager (`src/state/state_manager.py`)

Provides **versioned, immutable snapshots** of WorkbenchState:

```python
manager = StateManager()
v1 = manager.save_state(state)        # Returns version number
state = manager.get_state()           # Latest version
state = manager.get_state(version=1)  # Specific version
history = manager.get_state_history() # List of (version, timestamp, status)
manager.rollback(version=1)           # Appends old version as new (non-destructive)
```

---

## 11. Contradiction Detection

### `src/contradiction/detector.py`

The `ContradictionDetector` class runs 7 rules across all agent output pairs:

| Rule | What It Detects | Severity |
|------|----------------|----------|
| **CPI/SPI Direction** | One agent says improving, another says worsening | medium |
| **Risk Severity** | Agents assign different severity to same risk (requires 5+ shared words) | Based on gap |
| **Schedule Impact** | Duration estimates differ >50% (>2x = high) | Based on ratio |
| **Cost Estimate (EAC)** | Dollar amounts differ >10% (>25% = high) | Based on gap |
| **Root Cause** | Different root causes for same issue (needs 2+ shared domain terms) | medium |
| **Mitigation Conflict** | Conflicting actions (e.g., accelerate vs. defer, dual-source vs. sole-source) | high |
| **Confidence Disparity** | Same finding type from different agents with >0.3 confidence gap | Based on gap |

Key methods:
- `detect(agent_outputs) -> list[Contradiction]` — runs all 7 rules
- `classify_severity(contradictions) -> list[Contradiction]` — escalates based on patterns
- `suggest_resolution(contradiction) -> str` — context-aware resolution guidance

---

## 12. Observability Stack

### Logger (`src/observability/logger.py`)

JSON-structured logging to stderr + `logs/workbench.log`:

```python
from src.observability.logger import get_logger
logger = get_logger("my_component")
logger.info("Something happened", agent_name="cam_agent", trace_id="abc123")
```

Helper functions:
- `log_tool_call(agent, tool, params, result, latency_ms, trace_id)`
- `log_agent_event(agent, event_type, data, trace_id)`

### Tracer (`src/observability/tracer.py`)

Distributed-style trace correlation:

```python
tracer = Tracer()
trace_id = tracer.start_trace("explain variance")
span_id = tracer.start_span(trace_id, "cam_agent", "analyze_evm")
tracer.end_span(span_id, status="ok", metadata={"cpi": 0.87})
tracer.end_trace(trace_id, "completed")
report = ExecutionReport(tracer.get_trace(trace_id))
print(report.render())
```

### Metrics (`src/observability/metrics.py`)

Singleton collector with thread-safe counters:

```python
from src.observability.metrics import MetricsCollector
metrics = MetricsCollector()
metrics.record_tool_call("cam_agent", "read_evm_metrics", 45.2)
metrics.record_agent_execution("cam_agent", 1200, token_input=500, token_output=300)
summary = metrics.get_summary()  # Full stats with min/max/mean/p50/p95/p99
```

---

## 13. Memory System

### Memory Store (`src/memory/memory_store.py`)

Wraps ADK's `InMemoryMemoryService`. Pre-seeded with **15 program history facts** across
5 categories:

- **performance_trend** (3): CPI decline from 0.95 to 0.87, SPI drop, TCPI rise
- **recurring_pattern** (3): Wing assembly quality escapes, late ECNs, composite cure failures
- **past_decision** (3): Dual-sourcing deferral, rebaseline rejection, overtime authorization
- **contract_history** (3): 4 mods executed (+$7M), P00028 under negotiation, ceiling status
- **supplier_history** (3): Apex Fastener probation, Northwind preferred, Precision declining

### Memory Retrieval (`src/memory/memory_retrieval.py`)

TF-IDF keyword search without ML dependencies. Pre-populated with **20 contextual memories**
covering similar variance situations, contract precedents, supplier patterns, and quality
escape root causes from other defense programs.

```python
retriever = MemoryRetriever()
results = retriever.search_similar("CPI declining on fighter program", top_k=5)
```

Scoring: TF-IDF with 3x tag bonus weight. Excludes 50+ stopwords.

---

## 14. Mock Data & Demo Scenarios

### The Fictional Program

**Advanced Fighter Program (AFP)**
- Contract: FA8611-21-C-0042
- Prime: Meridian Aerospace Systems
- Type: CPIF (Cost Plus Incentive Fee)
- Phase: EMD (Engineering & Manufacturing Development)
- Budget: $485M
- Reporting Period: October 2024

**Current State (key metrics):**
- CPI: 0.87 (cost overrun)
- SPI: 0.88 (behind schedule)
- CV: -$2.1M
- SV: -$1.8M
- EAC: $557.5M (overrun from $485M BAC)
- 25 active risks
- 5 suppliers tracked
- 4 contract mods executed

### Demo Scenarios

**Scenario 1 — Variance Explanation:**
Trigger: "Explain the CPI and SPI drift this month. Wing assembly is driving cost overrun and there's a 30-day schedule slip on CDR."
Expected agents: CAM, RCA, SQ, Risk, PM

**Scenario 2 — Contract Change:**
Trigger: "Analyze the impact of contract modification P00028 for additional radar testing."
Expected agents: Contracts, CAM, Risk, PM

**Scenario 3 — Quality Escape:**
Trigger: "Investigate the quality escape on the wing root fitting from Apex Fasteners."
Expected agents: SQ, RCA, CAM, Contracts, Risk, PM

---

## 15. ADK Web UI — How It Works

### Agent Discovery

When you run `adk web adk_agents --port 8000`, ADK scans the `adk_agents/` directory for
Python packages that contain an `agent.py` file with a module-level `root_agent` variable.

**Required file structure per agent:**
```
adk_agents/
└── my_agent/
    ├── __init__.py      # Must contain: from . import agent
    └── agent.py         # Must define: root_agent = Agent(...)
```

### How Each Wrapper Works

Each `adk_agents/*/agent.py` file:
1. Adds the project root to `sys.path` (so `src.*` imports work)
2. Imports `get_model` from `src.config.model_config`
3. Imports `ToolRegistry` from `src.tools.tool_registry`
4. Creates a `ToolRegistry` and gets agent-specific tools
5. Creates a `root_agent = Agent(name=..., model=get_model(), ...)` at module level

### The Orchestrator Agent

`adk_agents/orchestrator/agent.py` is special — it gets ALL tools from the registry
(`registry.get_all_tools()`) and can perform the work of any specialist agent. This is
the recommended agent for general-purpose queries in the Web UI.

---

## 16. Testing

### Test Structure

```
tests/
├── test_agents.py      # 20 tests — creation, model check, prompts, tool assignment
├── test_tools.py       # ~40 tests — each tool function, registry operations
├── test_workflows.py   # ~17 tests — triage classification, parallel, refinement
└── test_scenarios.py   # ~22 tests — end-to-end (mostly skipped without async)
```

### Key Test Patterns

**Agent tests** verify:
- Agent name is correct
- Model is a `LiteLlm` instance with the expected model string (env-aware)
- System prompt contains required domain elements
- Tools are assigned correctly (by function name)
- All agents have unique names

**Tool tests** verify:
- Each read tool returns expected keys
- Analysis tools compute correct values
- Artifact tools create files in the correct output directories

**Workflow tests** verify:
- Intent classification maps keywords correctly
- Agent requirement mapping is correct
- Contradiction detection triggers on known conflicts
- State management versions correctly

### Running Tests

```bash
# Full suite
pytest

# Specific file
pytest tests/test_agents.py -v

# Specific test
pytest tests/test_agents.py::TestAgentCreation::test_create_pm_agent -v
```

**Known pre-existing failures** (5 in test_tools.py): `AttributeError` issues in
`test_calculate_risk_exposure`, `test_assess_supplier_risk`, `test_assess_contract_mod_impact`,
`test_get_tools_for_pm_agent`, and `test_get_tool_by_name`. These are unrelated to the
LLM provider refactor.

---

## 17. Dependencies

### `requirements.txt`

```
google-adk>=1.15.0           # Google Agent Development Kit (Agent, Runner, etc.)
google-genai>=1.0.0          # Google GenAI library
litellm>=1.0.0               # LLM abstraction layer (multi-provider routing)
anthropic>=0.18.0            # Anthropic SDK (needed if using Anthropic models)
openai>=1.0.0                # OpenAI SDK (needed if using OpenAI-compatible endpoints)
pydantic>=2.10.0             # Data validation and models
pydantic-settings>=2.6.0     # Settings management
python-dotenv>=1.0.0         # .env file loading
sentence-transformers>=2.2.0 # Sentence embeddings (used by memory system)
numpy>=1.24.0                # Numerical operations
pytest>=7.0.0                # Testing framework
pytest-asyncio>=0.21.0       # Async test support
```

### Key Dependency Notes

- `litellm` is the critical abstraction layer — it routes API calls to the correct provider
  based on the model string prefix
- `google-adk` provides the Agent, Runner, LiteLlm, SequentialAgent, ParallelAgent, and
  LoopAgent classes
- `anthropic` and `openai` are SDK packages that LiteLLM uses internally — you need
  whichever one matches your provider
- `sentence-transformers` is heavy (~500MB+ with model downloads) — the project actually
  uses a lightweight TF-IDF approach in `memory_retrieval.py` that does not require it,
  but the dependency exists for the `memory_store.py` ADK integration

---

## 18. Troubleshooting Guide

### LLM Connection Issues

**Problem: "API call failed" or connection timeout**
- Check that `LLM_API_BASE` is correct and reachable from your network
- Verify `LLM_API_KEY` is set correctly
- Test connectivity: `curl -k https://your-endpoint/v1/models -H "Authorization: Bearer YOUR_KEY"`
- If using internal endpoint, check VPN/proxy requirements

**Problem: SSL certificate verification error**
- Set `LLM_SSL_VERIFY=false` in your `.env`
- Or install your corporate CA cert and set `SSL_CERT_FILE=/path/to/ca-bundle.crt`

**Problem: "Model not found" or "Invalid model"**
- Verify the model string format: `provider/model-name`
- For internal endpoints: use `openai/your-model-name` (the `openai/` prefix is required)
- Check what models your endpoint supports: `curl -k https://your-endpoint/v1/models`

**Problem: Agent responds but output quality is poor**
- The system prompts were designed for Claude 3 Haiku / GPT-4 class models
- Smaller models may struggle with complex multi-step analysis
- Try simplifying the system prompts in `src/agents/*.py` for your model
- The tool calling format may need adjustment — test each agent individually first

### ADK Web UI Issues

**Problem: `adk web` command not found**
- Install Google ADK: `pip install google-adk>=1.15.0`
- Verify: `adk --version`

**Problem: Agent not appearing in Web UI**
- Check that `adk_agents/<name>/__init__.py` contains `from . import agent`
- Check that `adk_agents/<name>/agent.py` defines `root_agent` at module level
- Check for import errors: `python -c "from adk_agents.<name>.agent import root_agent"`

**Problem: Import errors when loading agents**
- The `adk_agents/*/agent.py` files add the project root to `sys.path`
- Make sure you run `adk web` from the project root directory
- Verify: `python -c "from src.config.model_config import get_model; print(get_model().model)"`

**Problem: "No module named src" error**
- You must run from the project root: `cd /path/to/adk-project && adk web adk_agents --port 8000`
- The `sys.path.insert(0, str(project_root))` in each wrapper handles this

### Test Issues

**Problem: Tests fail with model assertion error**
- The test reads `LLM_MODEL` from env — make sure it matches what's in your `.env`
- Default (no env var set) expects `anthropic/claude-3-haiku-20240307`
- If you changed `LLM_MODEL`, the test will expect that new value

**Problem: 5 pre-existing test failures in test_tools.py**
- These are `AttributeError` issues in `test_calculate_risk_exposure`, `test_assess_supplier_risk`,
  `test_assess_contract_mod_impact`, `test_get_tools_for_pm_agent`, `test_get_tool_by_name`
- They exist from before the refactor and are unrelated to LLM configuration

### Environment Variable Issues

**Problem: Agent still using Anthropic after changing .env**
- Make sure `.env` is in the project root directory
- Verify dotenv is loading: `python -c "from dotenv import load_dotenv; load_dotenv(); import os; print(os.getenv('LLM_MODEL'))"`
- If running with `adk web`, the env vars must be set before the process starts
- You can also export them directly: `export LLM_MODEL=openai/llama-3.3-70b-instruct`

**Problem: LLM_API_KEY not being used**
- `LLM_API_KEY` takes precedence when set
- If not set, LiteLLM falls back to `OPENAI_API_KEY` or `ANTHROPIC_API_KEY`
- Check precedence: set `LLM_API_KEY` explicitly for internal endpoints

---

## 19. Extending the Project

### Adding a New Agent

1. Create `src/agents/new_agent.py` following the pattern of any existing agent file
2. Define the system prompt and `create_new_agent()` function
3. Add tool assignments in `src/tools/tool_registry.py` → `_AGENT_TOOL_MAP`
4. Export from `src/agents/__init__.py`
5. Create `adk_agents/new_agent/__init__.py` (with `from . import agent`)
6. Create `adk_agents/new_agent/agent.py` with `root_agent = Agent(...)`
7. Add tests in `tests/test_agents.py`

### Adding a New Tool

1. Add the function to the appropriate file in `src/tools/` (data, analysis, or artifact)
2. Register it in `src/tools/tool_registry.py`:
   - Import the function
   - Add it to `_ALL_TOOLS` dict
   - Add it to relevant agents in `_AGENT_TOOL_MAP`
3. The `ToolRegistry` will automatically wrap it in a `FunctionTool`

### Connecting to Real Data

Replace the mock data imports in `src/tools/data_tools.py`:

```python
# Current (mock):
from src.mock_data.evm_data import EVM_METRICS

# Future (real):
# Option A: Database query
# Option B: API call to your program management system
# Option C: File read from shared drive
```

The tool function signatures and return types should remain the same so agents don't
need to change.

### Adding a New LLM Provider

If your provider implements the OpenAI `/v1/chat/completions` API:
- Just set `LLM_MODEL=openai/your-model` and `LLM_API_BASE=https://your-endpoint/v1`

If your provider has a unique API format:
- Check if LiteLLM already supports it: https://docs.litellm.ai/docs/providers
- If so, use the appropriate prefix (e.g., `cohere/command-r`, `together_ai/model`)
- If not, you would need to create a custom `BaseLlm` subclass in `src/config/`

---

## 20. Key Patterns & Conventions

### Error Handling in Tools
Every tool uses `_safe_call()` wrapper:
```python
def _safe_call(tool_name, params, fn):
    try:
        result = fn()
        log_tool_call(...)
        return result
    except Exception as exc:
        return {"error": f"{type(exc).__name__}: {exc}"}
```
Tools never raise exceptions to agents — they return error dicts.

### Agent Creation Pattern
```python
from src.config.model_config import get_model
from src.tools.tool_registry import ToolRegistry

def create_x_agent(registry=None):
    if registry is None:
        registry = ToolRegistry()
    tools = registry.get_tools_for_agent("x_agent")
    return Agent(name="x_agent", model=get_model(), instruction=PROMPT, tools=tools)
```

### ADK Web Wrapper Pattern
```python
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.config.model_config import get_model
from src.tools.tool_registry import ToolRegistry

registry = ToolRegistry()
tools = registry.get_tools_for_agent("x_agent")
model = get_model()

root_agent = Agent(name="x_agent", model=model, description="...", instruction="...", tools=tools)
```

### State Versioning
State is immutable and append-only. Every `save_state()` creates a new version.
`rollback()` creates a new version that is a copy of an old version (never destructive).

### Mock Data Convention
All mock data lives in `src/mock_data/*.py` as Python dicts/lists. Tool functions in
`data_tools.py` import and return this data. To switch to real data, only
`data_tools.py` needs to change.

---

*This document was generated on 2026-02-17 and reflects the state of the codebase after
the LLM provider abstraction refactor.*
