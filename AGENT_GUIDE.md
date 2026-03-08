# Program Execution Workbench — AI Agent Guide

> **Purpose of this document:** Full project context for an AI assistant working on this codebase. Covers architecture, every agent, every tool, all environment variables, the external assistant integration, and how to extend the project. Read this before touching any file.

---

## Table of Contents

1. [What This Project Is](#1-what-this-project-is)
2. [Project File Structure](#2-project-file-structure)
3. [How to Run](#3-how-to-run)
4. [Environment Variables Reference](#4-environment-variables-reference)
5. [Architecture Overview](#5-architecture-overview)
6. [LLM Configuration](#6-llm-configuration)
7. [Specialist Agents](#7-specialist-agents)
8. [Tool System — All 24 Tools](#8-tool-system--all-24-tools)
9. [External Assistant Integration (External Assistant)](#9-external-assistant-integration-rio-assistant)
10. [Workflow Pipeline](#10-workflow-pipeline)
11. [State Management](#11-state-management)
12. [Mock Data — The Simulated Program](#12-mock-data--the-simulated-program)
13. [ADK Web UI Agent Wrappers](#13-adk-web-ui-agent-wrappers)
14. [Observability Stack](#14-observability-stack)
15. [Memory System](#15-memory-system)
16. [Contradiction Detection](#16-contradiction-detection)
17. [Testing](#17-testing)
18. [How to Extend the Project](#18-how-to-extend-the-project)
19. [Troubleshooting](#19-troubleshooting)
20. [Key Patterns & Conventions](#20-key-patterns--conventions)

---

## 1. What This Project Is

**Program Execution Workbench** is a multi-agent AI system for acquisition program management. It uses Google ADK (Agent Development Kit) to orchestrate six specialist AI agents that analyze cost performance, schedule, risk, contracts, and supplier quality — and synthesize findings into executive-level reports.

### Primary use cases
- Explain a cost or schedule variance (EVM analysis)
- Assess and update the program risk register
- Investigate a quality escape from a supplier
- Evaluate contract modification impacts
- Generate leadership briefs, 8D reports, CAM narratives, and action item lists

### Key technology choices
| Component | Technology |
|-----------|-----------|
| Agent framework | [Google ADK](https://google.github.io/adk-docs/) (`google-adk>=1.15.0`) |
| LLM abstraction | LiteLLM (via `google.adk.models.lite_llm.LiteLlm`) |
| Default LLM | Anthropic Claude 3 Haiku (switchable via env vars) |
| External assistant | OpenAI Assistants API (configurable endpoint) |
| Data | Python mock data modules (no database needed) |
| Output | Markdown files written to `outputs/` |

---

## 2. Project File Structure

```
adk-project/
│
├── .env.example              # All env var templates — copy to .env
├── .env                      # Your local config (gitignored)
├── .gitignore
├── pyproject.toml            # Package definition and dependencies
├── requirements.txt          # pip-installable deps
├── pytest.ini                # Test config (asyncio_mode=auto)
├── README.md                 # User-facing readme
├── PROJECT_GUIDE.md          # Prior project guide (may be outdated)
├── AGENT_GUIDE.md            # This file — comprehensive AI guide
│
├── run_workbench.py          # CLI entry point for orchestrated demos
├── run_workbench.bat         # Windows equivalent
│
├── src/                      # Core application source
│   ├── __init__.py
│   │
│   ├── config/
│   │   └── model_config.py   # get_model() — LiteLlm from env vars
│   │
│   ├── agents/               # Specialist agent implementations
│   │   ├── __init__.py       # Exports all create_*_agent() functions
│   │   ├── pm_agent.py       # Program Manager
│   │   ├── cam_agent.py      # Control Account Manager
│   │   ├── rca_agent.py      # Root Cause Analysis
│   │   ├── risk_agent.py     # Risk Management (+ External Assistant tool)
│   │   ├── contracts_agent.py # Contracts & FAR/DFARS
│   │   └── sq_agent.py       # Supplier Quality
│   │
│   ├── workflows/            # Multi-agent orchestration
│   │   ├── orchestrator.py   # Main WorkbenchOrchestrator class
│   │   ├── triage.py         # Intent classification
│   │   ├── parallel_analysis.py # Concurrent agent execution
│   │   └── refinement.py     # LoopAgent contradiction resolution
│   │
│   ├── tools/                # All agent tool functions
│   │   ├── tool_registry.py  # ToolRegistry — maps agents to tools
│   │   ├── data_tools.py     # 10 read tools (EVM, risks, milestones, etc.)
│   │   ├── analysis_tools.py # 8 compute tools (EAC, exposure, variance)
│   │   ├── artifact_tools.py # 6 write tools (briefs, 8D, risk updates)
│   │   └── external_assistant_tool.py  # External Assistant bridge (External platform)
│   │
│   ├── state/
│   │   ├── models.py         # 15+ Pydantic domain models
│   │   └── state_manager.py  # Versioned state snapshots
│   │
│   ├── contradiction/
│   │   └── detector.py       # 7-rule contradiction detection engine
│   │
│   ├── observability/
│   │   ├── logger.py         # Structured JSON logging
│   │   ├── tracer.py         # Distributed-style trace correlation
│   │   └── metrics.py        # Metrics collection
│   │
│   ├── memory/
│   │   ├── memory_store.py   # 15 pre-seeded program history facts
│   │   └── memory_retrieval.py
│   │
│   └── mock_data/            # Simulated Advanced Fighter Program data
│       ├── program_data.py
│       ├── evm_data.py       # CPI=0.87, SPI=0.88, wing assembly in red
│       ├── ims_data.py
│       ├── risk_data.py      # 25 risks; R-001 is critical (5x5=25)
│       ├── contract_data.py
│       └── supplier_data.py  # Apex Fastener on probation
│
├── adk_agents/               # ADK Web UI entry points (one per agent)
│   ├── __init__.py
│   ├── pm_agent/             # Each sub-dir: __init__.py + agent.py
│   ├── cam_agent/
│   ├── rca_agent/
│   ├── risk_agent/
│   ├── contracts_agent/
│   ├── sq_agent/
│   └── orchestrator/         # Has ALL tools (full workbench)
│
├── demos/                    # Runnable scenario scripts
│   ├── demo_runner.py
│   ├── scenario_1_variance.py
│   ├── scenario_2_contract_change.py
│   └── scenario_3_quality_escape.py
│
├── tests/                    # pytest test suite
│   ├── test_agents.py
│   ├── test_tools.py
│   ├── test_workflows.py
│   └── test_scenarios.py
│
└── outputs/                  # Generated artifacts (gitignored)
    ├── briefs/
    └── artifacts/
```

---

## 3. How to Run

### Prerequisites
```bash
pip install -e .          # Install the package + deps
cp .env.example .env      # Create your local config
# Edit .env with your API keys (see Section 4)
```

### ADK Web UI (primary interface)
```bash
# Launch any individual agent
adk web adk_agents --port 8000

# The web UI auto-discovers all agents in adk_agents/:
#   pm_agent, cam_agent, rca_agent, risk_agent,
#   contracts_agent, sq_agent, orchestrator
```
Then open http://localhost:8000, select an agent from the dropdown, and chat.

### Run demos programmatically
```bash
python run_workbench.py --scenario variance
python run_workbench.py --scenario contract_change
python run_workbench.py --scenario quality_escape
python run_workbench.py --all
```

### Run tests
```bash
pytest tests/ -v
pytest tests/test_agents.py -v       # Agent tests only
pytest tests/test_tools.py -v        # Tool tests only
```

---

## 4. Environment Variables Reference

Copy `.env.example` to `.env`. You only need to set the keys relevant to your LLM provider and the features you want.

### LLM Configuration (affects all agents)

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_MODEL` | `anthropic/claude-3-haiku-20240307` | LiteLLM model string. Format: `provider/model-name` |
| `LLM_API_BASE` | _(none)_ | Custom base URL for OpenAI-compatible endpoints |
| `LLM_API_KEY` | _(none)_ | API key override. Falls back to provider-specific keys below |
| `LLM_SSL_VERIFY` | `true` | Set to `false` for self-signed certs |

**Common LLM_MODEL values:**
```bash
LLM_MODEL=anthropic/claude-3-haiku-20240307   # Anthropic (cheapest/fastest)
LLM_MODEL=anthropic/claude-3-5-sonnet-latest  # Anthropic (best quality)
LLM_MODEL=openai/gpt-4o                        # OpenAI
LLM_MODEL=openai/gpt-4o-mini                   # OpenAI (cheaper)
LLM_MODEL=openai/gpt-oss-120b                  # Custom model on OpenAI-compatible endpoint
```

### Provider API Keys

| Variable | Description |
|----------|-------------|
| `ANTHROPIC_API_KEY` | Required when using any `anthropic/*` model |
| `OPENAI_API_KEY` | Required when using any `openai/*` model |

### External External Assistant Integration

These power the `call_external_assistant` tool in the `risk_agent`. See `.env.example` for the full list of `LMCO_*` variables and their descriptions.

### Using an external OpenAI-compatible endpoint as the orchestrator LLM

To route all agent LLM calls through an external chat completions endpoint:
```bash
LLM_MODEL=openai/gpt-4o
LLM_API_BASE=https://your-endpoint/v1
LLM_API_KEY=<your-bearer-token>
LLM_SSL_VERIFY=false
```

### Application Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `LOG_LEVEL` | `INFO` | Python logging level |
| `MAX_REFINEMENT_ITERATIONS` | `3` | Max contradiction-resolution loops |

---

## 5. Architecture Overview

```
User (adk web or demo script)
         │
         ▼
┌──────────────────────────────────────────────────────────────┐
│                  WorkbenchOrchestrator                       │
│  src/workflows/orchestrator.py                               │
│                                                              │
│  Phase 1: Triage (classify_intent → get_required_agents)     │
│  Phase 2: Parallel Analysis (run all specialist agents)      │
│  Phase 3: Contradiction Detection + Refinement (LoopAgent)   │
│  Phase 4: Synthesis (PM Agent → leadership brief)            │
└────────────────────────┬─────────────────────────────────────┘
                         │
         ┌───────────────┼───────────────────┐
         ▼               ▼                   ▼
   ┌──────────┐   ┌──────────────┐   ┌──────────────┐
   │ cam_agent │   │  rca_agent   │   │  risk_agent  │
   │ EVM/cost  │   │ Root cause   │   │ Risk 5x5     │
   │ variance  │   │ 5W/8D/Fish   │   │ + Risk tool   │
   └──────────┘   └──────────────┘   └──────────────┘
         ▼               ▼                   ▼
   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐
   │contracts_agent│  │   sq_agent   │   │   pm_agent   │
   │ FAR/DFARS     │  │ Supplier/    │   │ Synthesizer  │
   │ contract mods │  │ Quality      │   │ Brief writer │
   └──────────────┘  └──────────────┘   └──────────────┘
         │
         ▼
┌──────────────────────────────────────────────────────────────┐
│                      Tool Registry                           │
│  src/tools/tool_registry.py                                  │
│  24 tools (10 data + 8 analysis + 6 artifact + call_ext_assistant)     │
│  Each agent gets only its permitted subset                   │
└──────────────────────────────────────────────────────────────┘
         │
         ├── read_* tools → src/mock_data/ (simulated program)
         ├── calculate_* / assess_* tools → inline Python logic
         ├── write_* tools → outputs/ directory (Markdown files)
         └── call_external_assistant → External Assistants API
```

**ADK Web UI mode** (simpler — used most often):
Each `adk_agents/<name>/agent.py` defines a standalone `root_agent` with its own tools. The agents don't orchestrate each other in this mode — each is a self-contained specialist chatbot.

---

## 6. LLM Configuration

**`src/config/model_config.py`** contains one function used by every agent:

```python
from src.config.model_config import get_model

model = get_model()   # Returns LiteLlm instance from env vars
```

All agents call `get_model()` — changing your `.env` switches the LLM for every agent with no code changes.

**To use a custom OpenAI-compatible endpoint:**
```bash
LLM_MODEL=openai/gpt-4o
LLM_API_BASE=https://your-endpoint/v1
LLM_API_KEY=<bearer-token>
LLM_SSL_VERIFY=false
```

**Important:** `LiteLlm` requires the `openai/` prefix even for OpenAI-compatible non-OpenAI endpoints. The prefix tells LiteLLM which client adapter to use.

---

## 7. Specialist Agents

Each agent is defined in `src/agents/<name>.py` with:
1. A system prompt constant (`*_SYSTEM_PROMPT`)
2. A factory function `create_<name>_agent(registry=None) -> Agent`

All agents use `get_model()` and pull their tools from `ToolRegistry`.

---

### 7.1 PM Agent (`pm_agent`)
**File:** `src/agents/pm_agent.py`
**Role:** Executive synthesizer. Consolidates findings from all specialists into leadership communications.

**Framework:** What / Why / So What / Now What

**Tools:** All 6 artifact writers + `read_program_snapshot` + `read_evm_metrics` + `calculate_eac`

**When to use in adk web:** For generating leadership briefs, synthesizing multiple data sources, or getting an executive summary of the program.

---

### 7.2 CAM Agent (`cam_agent`)
**File:** `src/agents/cam_agent.py`
**Role:** Control Account Manager — Earned Value Management expert.

**Specialties:**
- EVM analysis (CPI, SPI, CV, SV)
- EAC projections (CPI method, SPI*CPI composite, management estimate)
- Variance driver identification by work package
- CPI trend analysis and projected completion performance

**Tools:** `read_evm_metrics`, `read_evm_history`, `read_ims_milestones`, `calculate_eac`, `calculate_variance_drivers`, `analyze_cpi_trend`, `write_cam_narrative`, `write_action_items`

---

### 7.3 RCA Agent (`rca_agent`)
**File:** `src/agents/rca_agent.py`
**Role:** Root Cause Analysis specialist.

**Methodologies:**
- **5 Whys** — sequential causal chain
- **Fishbone (Ishikawa)** — category-based (6Ms: Man, Machine, Material, Method, Measurement, Milieu)
- **8D Problem Solving** — structured 8-discipline report (D1 Team → D8 Congratulations)

**Confidence levels:** High (>80%), Medium (50-80%), Low (<50%)

**Tools:** `read_evm_metrics`, `read_ims_milestones`, `read_supplier_metrics`, `read_quality_escape_data`, `write_eight_d_report`

---

### 7.4 Risk Agent (`risk_agent`)
**File:** `src/agents/risk_agent.py`
**Role:** Risk management using the 5x5 probability × impact matrix. **Has the External Assistant integration.**

**Risk Score Thresholds:**
| Score | Color | Action |
|-------|-------|--------|
| 1–4 | 🟢 Green | Accept and monitor |
| 5–9 | 🟡 Yellow | Active management required |
| 10–16 | 🟠 Orange | Mitigation mandatory |
| 17–25 | 🔴 Red | Immediate action required |

**Risk Categories:** Technical, Schedule, Cost, Supply Chain, Requirements, External

**Tools:** `read_risk_register`, `read_evm_metrics`, `read_supplier_metrics`, `calculate_risk_exposure`, `assess_supplier_risk`, `write_risk_register_update`, **`call_external_assistant`**

**External Assistant workflow (built into system prompt):**
1. Call data tools to gather program state
2. Compose query with context (CPI, SPI, risk IDs, etc.)
3. Call `call_external_assistant(query)` → get Risk domain expert analysis
4. Incorporate response into final assessment
5. Call `write_risk_register_update` to document

---

### 7.5 Contracts Agent (`contracts_agent`)
**File:** `src/agents/contracts_agent.py`
**Role:** Contract administration with FAR/DFARS compliance expertise.

**Contract type expertise:** CPIF, CPFF, FFP, T&M, IDIQ

**Key FAR clauses:**
- FAR 52.243 — Changes
- FAR 52.249 — Termination
- DFARS 252.234 — EVMS

**Tools:** `read_contract_baseline`, `read_contract_mods`, `read_cdrl_list`, `assess_contract_mod_impact`, `write_contract_change_summary`

---

### 7.6 S/Q Agent (`sq_agent`)
**File:** `src/agents/sq_agent.py`
**Role:** Supplier performance monitoring and quality escape investigation.

**Key metrics:**
- OTDP — On-Time Delivery Performance (target: ≥95%)
- DPMO — Defects Per Million Opportunities (target: <1000)
- Quality Rating (target: ≥90)

**Quality escape response protocol:** Contain → Identify → Notify → Investigate → Correct → Prevent → Verify

**COPQ categories:** Rework Labor, Scrap Material, NDI Inspection, Engineering Disposition, Schedule Delay Cost

**Tools:** `read_supplier_metrics`, `read_quality_escape_data`, `assess_supplier_risk`, `calculate_cost_of_poor_quality`, `write_action_items`, `write_eight_d_report`

---

## 8. Tool System — All 24 Tools

Tools live in `src/tools/`. They are Python functions wrapped in `FunctionTool` by `ToolRegistry`. Agents only receive the tools mapped to them in `_AGENT_TOOL_MAP`.

### Agent → Tool Mapping

```
pm_agent:         write_leadership_brief, write_cam_narrative, write_risk_register_update,
                  write_action_items, write_eight_d_report, write_contract_change_summary,
                  read_program_snapshot, read_evm_metrics, calculate_eac

cam_agent:        read_evm_metrics, read_evm_history, read_ims_milestones,
                  calculate_eac, calculate_variance_drivers, analyze_cpi_trend,
                  write_cam_narrative, write_action_items

rca_agent:        read_evm_metrics, read_ims_milestones, read_supplier_metrics,
                  read_quality_escape_data, write_eight_d_report

risk_agent:       read_risk_register, read_evm_metrics, read_supplier_metrics,
                  calculate_risk_exposure, assess_supplier_risk,
                  write_risk_register_update, call_external_assistant

contracts_agent:  read_contract_baseline, read_contract_mods, read_cdrl_list,
                  assess_contract_mod_impact, write_contract_change_summary

sq_agent:         read_supplier_metrics, read_quality_escape_data,
                  assess_supplier_risk, calculate_cost_of_poor_quality,
                  write_action_items, write_eight_d_report

orchestrator:     ALL tools (24 total)
```

---

### 8.1 Data Tools (`src/tools/data_tools.py`)

All return dicts. All log via `log_tool_call`. All wrap mock data modules.

| Function | Returns |
|----------|---------|
| `read_program_snapshot()` | Contract metadata, WBS structure, key personnel, budget summary |
| `read_evm_metrics()` | CPI, SPI, CV, SV, BCWP, BCWS, ACWP, BAC, EAC, VAC, TCPI, work packages |
| `read_evm_history()` | 6-month EVM trending (Apr–Oct 2024), period summaries |
| `read_ims_milestones()` | All milestones, critical path, at-risk count, schedule margin |
| `read_risk_register()` | 25 risks with full fields + summary stats (by level, status, cost exposure) |
| `read_contract_baseline()` | Contract number, type, value, fee structure, CLINs, EVMS clause |
| `read_contract_mods(mod_number="")` | Modifications, optionally filtered by mod number (case-insensitive) |
| `read_cdrl_list()` | CDRL items with status and submission dates |
| `read_supplier_metrics(supplier_name="")` | Supplier OTDP/DPMO/ratings/CARs, optionally filtered |
| `read_quality_escape_data()` | Quality escape event with severity, cost breakdown, containment actions |

---

### 8.2 Analysis Tools (`src/tools/analysis_tools.py`)

| Function | Key Parameters | Returns |
|----------|---------------|---------|
| `calculate_eac(method="cpi")` | `method`: "cpi", "spi_cpi", "management" | eac, vac, vac_pct, tcpi_against_eac |
| `assess_schedule_criticality(milestone_name)` | Partial match on milestone title | slip_days, is_critical_path, impact_assessment, downstream_milestones |
| `calculate_variance_drivers(threshold_percent=5.0)` | Threshold for CV%/SV% to qualify as driver | drivers sorted by magnitude, counts, total CV/SV |
| `calculate_risk_exposure()` | _(none)_ | risk_exposures (prob × cost), total_cost_exposure, top_risk |
| `assess_supplier_risk(supplier_name)` | Full or partial supplier name | overall_risk_level, risk_score (0–100), contributing_factors, recommendations |
| `calculate_cost_of_poor_quality(event_type="quality_escape")` | _(type string)_ | COPQ breakdown, total, % of BAC |
| `analyze_cpi_trend()` | _(none)_ | trend_direction, avg_change_per_period, projected_cpi_at_completion |
| `assess_contract_mod_impact(mod_number)` | Exact mod number (e.g., "P00025") | cost_impact, schedule_impact_weeks, CLINs affected, cumulative mods |

---

### 8.3 Artifact Tools (`src/tools/artifact_tools.py`)

All write Markdown files to `outputs/` and return `{"filepath": "...", "content": "..."}`.

| Function | Output Path | Key Parameters |
|----------|-------------|---------------|
| `write_leadership_brief(...)` | `outputs/briefs/{ts}_leadership_brief.md` | program_name, intent, what_happened, why_it_happened, so_what, now_what, risk_level |
| `write_cam_narrative(...)` | `outputs/artifacts/{ts}_cam_narrative_{wbs_id}.md` | wbs_id, wbs_name, variance_explanation, corrective_actions, eac_impact |
| `write_risk_register_update(...)` | `outputs/artifacts/{ts}_risk_update_{risk_id}.md` | risk_id, title, probability, impact, mitigation, status, justification |
| `write_action_items(items)` | `outputs/artifacts/{ts}_action_items.md` | items: JSON string of list `[{action, owner, due_date, priority, status}]` |
| `write_eight_d_report(...)` | `outputs/artifacts/{ts}_eight_d_report.md` | problem_description, containment, root_cause, corrective_action, preventive_action, verification |
| `write_contract_change_summary(...)` | `outputs/artifacts/{ts}_contract_change_{mod}.md` | mod_number, description, cost_impact, schedule_impact, new_obligations, recommendation |

---

### 8.4 External Tool — External Assistant (`src/tools/external_assistant_tool.py`)

See Section 9 for full details.

| Function | Parameters | Returns |
|----------|-----------|---------|
| `call_external_assistant(query)` | `query: str` — risk scenario or question with context | `{status, response, assistant, thread_id}` or `{status, error}` |

---

## 9. External Assistant Integration (External Assistant)

### What it is

The `call_external_assistant` tool bridges the ADK `risk_agent` to a pre-built OpenAI Assistant hosted on an external platform. The Risk (Risk, Issue, Opportunity) Assistant has:
- Custom system instructions for Risk management
- A vector store with reference documents

### Why it's a tool (not the LLM)

ADK uses the chat completions API format for its LLM calls. The External Assistant uses the OpenAI **Assistants API** — a different protocol involving threads, runs, polling, and message retrieval. Wrapping it as a tool is the clean integration point: the risk_agent's "brain" (any LLM) orchestrates tool calls, and delegates Risk-specific analysis to this tool.

### How it works (source: `src/tools/external_assistant_tool.py`)

```python
def call_external_assistant(query: str) -> dict:
    # 1. POST /v1/threads/runs
    #    Body: {assistant_id, thread: {messages: [{role:user, content:query}]}}
    #    Headers: Authorization: Bearer <token>
    #             OpenAI-Beta: assistants=v2

    # 2. Poll GET /v1/threads/{thread_id}/runs/{run_id}
    #    Until status in {completed, failed, cancelled, expired}

    # 3. GET /v1/threads/{thread_id}/messages
    #    Extract first assistant message content block of type "text"

    # Returns: {status, response, assistant, thread_id}
```

### Configuration (`.env`)

All configuration is via environment variables. See `.env.example` for the full list of `LMCO_*` variables. The key ones:
- `LMCO_API_KEY` — Bearer token (required)
- `LMCO_API_BASE` — Assistants API base URL (required)
- `LMCO_Risk_ASSISTANT_ID` — Assistant ID (required)

### Adding a new external assistant

To add a second assistant (e.g., the CAM Assistant):

1. Add a new function to `src/tools/external_assistant_tool.py`:
```python
def call_cam_assistant(query: str) -> dict:
    """Query the CAM Assistant for EVM guidance."""
    cfg = _get_config()
    cfg["assistant_id"] = os.getenv("LMCO_CAM_ASSISTANT_ID", "")
    # ... rest of implementation (identical to call_external_assistant)
```

2. Register in `tool_registry.py`:
```python
from src.tools.external_assistant_tool import call_external_assistant, call_cam_assistant
```

3. Add env var to `.env.example`

---

## 10. Workflow Pipeline

**Used only in programmatic mode** (`run_workbench.py` / demos). `adk web` uses single-agent mode.

### Phase 1: Triage (`src/workflows/triage.py`)
- `classify_intent(trigger)` → `(intent: str, confidence: float)`
- Keyword matching against 5 intents: `variance_explanation`, `contract_change`, `quality_escape`, `risk_assessment`, `schedule_analysis`
- `get_required_agents(intent)` → list of agent names to run

### Phase 2: Parallel Analysis (`src/workflows/parallel_analysis.py`)
- `create_parallel_analysis_workflow(required_agents, registry)` → `ParallelAgent`
- Runs all specialist agents concurrently via ADK's `ParallelAgent`
- Returns map of `agent_name → AgentOutput`

### Phase 3: Contradiction Detection + Refinement
- `ContradictionDetector.detect(agent_outputs)` → `list[Contradiction]` (7 detection rules)
- `create_refinement_workflow(registry)` → `LoopAgent` (max iterations from env)
- LoopAgent iterates until contradictions resolved or limit reached

### Phase 4: Synthesis
- PM Agent receives all findings and writes leadership brief
- `write_leadership_brief(...)` called as tool

---

## 11. State Management

**`src/state/models.py`** — Pydantic models for everything:

```python
WorkbenchState          # Top-level: case_file, agent_outputs, contradictions, status
  └── CaseFile          # Intent, trigger, program_name, required_agents
  └── AgentOutput       # findings[], confidence, execution_time_ms, errors[]
       └── Finding      # agent_name, type, content, confidence, evidence_refs
  └── Contradiction     # finding_a, finding_b, description, severity, resolved
  └── WorkbenchStatus   # triaging | analyzing | refining | synthesizing | complete

# Domain models
EVMMetrics, IMSMilestone, WorkPackage, RiskItem, ContractMod, SupplierMetric
```

**`src/state/state_manager.py`** — Append-only versioned snapshots:
```python
manager = StateManager()
version = manager.save_state(state)        # Create snapshot, returns int version
state = manager.get_state()                # Latest snapshot
state = manager.get_state(version=2)       # Specific version
state = manager.rollback(version=1)        # Roll back (creates new version)
history = manager.get_state_history()      # [(version, timestamp, status), ...]
```

---

## 12. Mock Data — The Simulated Program

All data represents the **Advanced Fighter Program (AFP)** — a fictional but realistic program with deliberate problems for demo/testing purposes.

### Program Health at a Glance

| Metric | Value | Status |
|--------|-------|--------|
| CPI | 0.87 | 🔴 Cost overrun |
| SPI | 0.88 | 🔴 Schedule slip |
| TCPI (BAC) | 1.15 | 🔴 Tight to-complete performance |
| EAC | $557.5M | — |
| BAC | $485M | — |
| VAC | -$72.5M | 🔴 $72M overrun projected |
| Worst WBS | 1.3.2 Wing Assembly | CPI=0.72, SPI=0.69 |

### Key Issues Embedded in the Data
- **Apex Fastener** on supplier probation (OTDP 72%, DPMO 4500)
- **Wing Assembly (R-001)** is the critical risk (5×5=25 score)
- **P00028** contract mod under negotiation (~$1.8M flight test instrumentation)
- EAC of $557.5M exceeds adjusted ceiling of $492M by $65.5M (Nunn-McCurdy territory)
- Schedule rebaseline was proposed but rejected by PEO

### Data modules
| Module | Contains |
|--------|---------|
| `program_data.py` | PROGRAM_SNAPSHOT: contract, WBS structure, personnel |
| `evm_data.py` | EVM_METRICS + EVM_HISTORY (6 months) |
| `ims_data.py` | Milestones, critical path, IMS summary |
| `risk_data.py` | RISK_REGISTER (25 risks) + RISK_SUMMARY |
| `contract_data.py` | CONTRACT_BASELINE + MODIFICATIONS (P00024–P00027 + pending P00028) |
| `supplier_data.py` | Apex Fastener, Northwind Composites, Precision Avionics, others |

---

## 13. ADK Web UI Agent Wrappers

`adk_agents/<name>/agent.py` files are the entry points for `adk web`. Each:

1. Adds project root to `sys.path` (so `src.*` imports work)
2. Calls `ToolRegistry()` and `get_tools_for_agent(name)`
3. Calls `get_model()` for the LLM
4. Defines `root_agent = Agent(...)` — **must be named `root_agent`**

```python
# adk_agents/risk_agent/agent.py
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from google.adk import Agent
from src.config.model_config import get_model
from src.tools.tool_registry import ToolRegistry

registry = ToolRegistry()
tools    = registry.get_tools_for_agent("risk_agent")
model    = get_model()

root_agent = Agent(
    name="risk_agent",
    model=model,
    description="Risk Management Agent...",
    instruction=RISK_SYSTEM_PROMPT,  # imported from src.agents.risk_agent
    tools=tools,
)
```

**`adk_agents/__init__.py`** must exist (even if empty) so ADK treats the directory as a Python package.

**`adk_agents/<name>/__init__.py`** must exist and should contain: `from . import agent`

The `orchestrator` agent in `adk_agents/orchestrator/agent.py` gets `registry.get_all_tools()` — all 24 tools.

---

## 14. Observability Stack

### Logging (`src/observability/logger.py`)
- Structured JSON to `logs/` directory
- Helper functions: `log_tool_call(agent, tool, params, result, latency_ms)`, `log_agent_event(agent, event_type, data)`
- Every data tool call is automatically logged via `_safe_call()`

### Tracing (`src/observability/tracer.py`)
```python
tracer = Tracer()
trace_id = tracer.start_trace(intent="variance_explanation")
span_id  = tracer.start_span(trace_id, agent_name="cam_agent", operation="evm_analysis")
tracer.end_span(span_id, status="ok", metadata={"cpi": 0.87})
tracer.end_trace(trace_id, status="completed")
tracer.export_trace(trace_id, "outputs/trace.json")
report = ExecutionReport(tracer.get_trace(trace_id)).render()
```

### Metrics (`src/observability/metrics.py`)
- `MetricsCollector` class for runtime performance data

---

## 15. Memory System

**`src/memory/memory_store.py`** — Pre-seeded with 15 program history facts in 5 categories:

| Category | Count | Examples |
|----------|-------|---------|
| `performance_trend` | 3 | CPI decline 0.94→0.87 over 6 months |
| `recurring_pattern` | 3 | Wing assembly quality escapes, ECN disruptions |
| `past_decision` | 3 | Dual-source deferred, overtime authorized |
| `contract_history` | 3 | 4 mods totalling +$7M, EAC exceeds ceiling |
| `supplier_history` | 3 | Apex probation, Northwind preferred, Precision Avionics CARs |

```python
from src.memory.memory_store import WorkbenchMemoryStore

store = WorkbenchMemoryStore()
context = store.get_preloaded_context()    # Formatted string for agent prompts
mems = store.get_memories_by_tag("quality")
mems = store.get_memories_by_category("past_decision")
store.add_memory(content="...", author="cam_agent", tags=["evm", "variance"])
```

---

## 16. Contradiction Detection

**`src/contradiction/detector.py`** — `ContradictionDetector` runs 7 rules over all findings:

| Rule | What it detects |
|------|----------------|
| 1 | CPI/SPI trend direction disagreement between agents |
| 2 | Risk severity conflict (one says critical, another says low) |
| 3 | Schedule impact mismatch (different timeline estimates) |
| 4 | EAC estimate divergence between agents |
| 5 | Root cause disagreement |
| 6 | Mitigation strategy conflict |
| 7 | Confidence disparity on same finding type |

Returns `list[Contradiction]` with severity (low/medium/high), description, and suggested resolution strategy.

---

## 17. Testing

```
tests/
├── test_agents.py    # Agent creation, model type, tool count
├── test_tools.py     # Each tool returns expected keys, handles errors
├── test_workflows.py # Triage, parallel, refinement workflow tests
└── test_scenarios.py # End-to-end scenario validation
```

**Key test pattern:**
```python
import pytest
from unittest.mock import patch

@pytest.mark.asyncio
async def test_cam_agent_evm_analysis():
    registry = ToolRegistry()
    agent = create_cam_agent(registry)
    assert agent.name == "cam_agent"
    assert len(agent.tools) == 8
    assert isinstance(agent.model, LiteLlm)
```

Tests read `LLM_MODEL` from env so they work with any configured provider.

---

## 18. How to Extend the Project

### Add a new specialist agent

1. **Create `src/agents/my_agent.py`:**
```python
from google.adk import Agent
from src.config.model_config import get_model
from src.tools.tool_registry import ToolRegistry

MY_SYSTEM_PROMPT = """You are..."""

def create_my_agent(registry=None):
    if registry is None:
        registry = ToolRegistry()
    return Agent(
        name="my_agent",
        model=get_model(),
        instruction=MY_SYSTEM_PROMPT,
        tools=registry.get_tools_for_agent("my_agent"),
    )
```

2. **Register tools in `src/tools/tool_registry.py`:**
```python
_AGENT_TOOL_MAP["my_agent"] = [
    read_program_snapshot,
    my_new_tool,
]
```

3. **Export from `src/agents/__init__.py`:**
```python
from src.agents.my_agent import create_my_agent
```

4. **Create `adk_agents/my_agent/__init__.py`** (contains: `from . import agent`)

5. **Create `adk_agents/my_agent/agent.py`** (define `root_agent`)

### Add a new tool

1. **Write the function** in the appropriate tools file (or a new one):
```python
def my_new_tool(param: str) -> dict:
    """Docstring becomes the LLM's description of this tool.

    Args:
        param: Description of what this parameter does.

    Returns:
        Dict with result data.
    """
    # implementation
    return {"result": "..."}
```

2. **Import and register** in `tool_registry.py`:
```python
from src.tools.my_tools import my_new_tool
_AGENT_TOOL_MAP["risk_agent"].append(my_new_tool)
```

### Add a new external assistant tool

See Section 9. Pattern: copy `call_external_assistant`, change the assistant ID env var, add to registry.

### Connect real data

Replace the mock data modules in `src/mock_data/` with API calls or database queries. Tool function signatures and return shapes must stay the same — agents depend on the key names (e.g., `result["CPI"]`, `result["risks"]`).

---

## 19. Troubleshooting

### `ModuleNotFoundError: No module named 'src'`
The `adk_agents/` wrappers add the project root to `sys.path`. If running scripts from outside the project, either:
```bash
pip install -e .          # Install as editable package
# or
export PYTHONPATH=/path/to/adk-project
```

### `ModuleNotFoundError: No module named 'google.adk'`
```bash
pip install google-adk>=1.15.0
# or
pip install -e .
```

### `call_external_assistant` returns `{"status": "error", "error": "No API key found"}`
Set the required `LMCO_*` env vars in your `.env` file. See `.env.example` for the full list.

### `call_external_assistant` returns SSL errors
Set `LMCO_SSL_VERIFY=false` in your `.env`. If you're still getting SSL errors, verify `urllib3` is installed and `_get_config()` returns `ssl_verify=False`.

### `call_external_assistant` times out
The External Assistant can take 10–30 seconds. Increase `LMCO_POLL_TIMEOUT` if the network is slow.

### LiteLlm `AuthenticationError`
Check your API key env var. For Anthropic: `ANTHROPIC_API_KEY`. For OpenAI-compatible endpoints: `LLM_API_KEY`.

### `adk web` shows no agents
Each agent directory needs both `__init__.py` (containing `from . import agent`) and `agent.py` (defining `root_agent`). Check both files exist and `root_agent` is defined at module level (not inside a function).

### Tool not being called by agent
1. Check the tool is in `_AGENT_TOOL_MAP` for that agent in `tool_registry.py`
2. Check the tool's docstring — this is what the LLM reads to decide whether to call it
3. Check the function signature — parameter names and types must be clear

---

## 20. Key Patterns & Conventions

### Pattern: Factory functions for agents
All agents use `create_<name>_agent(registry=None)` pattern. This allows dependency injection in tests and lazy initialization.

### Pattern: Tool registry as single source of truth
Never instantiate `FunctionTool` directly outside `ToolRegistry`. All tool wrapping happens in one place.

### Pattern: Environment-driven LLM configuration
`get_model()` is the only place LiteLlm is instantiated. Change LLM provider by editing `.env` only.

### Pattern: Tool return type is always `dict`
All tool functions return dicts. On error: `{"error": "..."}`. On success: relevant keys. Agents handle both shapes.

### Pattern: `root_agent` must be a module-level variable
ADK Web discovers `root_agent` by importing the module and looking for this name. It cannot be inside a function or class.

### Pattern: sys.path injection in adk_agents wrappers
```python
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
```
This must be the first thing in each `adk_agents/<name>/agent.py` — before any `src.*` imports.

### Convention: Tool docstrings are prompts
The LLM reads tool docstrings to decide when and how to call a tool. Write docstrings as if explaining to an AI:
- First line: what this tool does and when to use it
- Args section: what each parameter means and valid values
- Returns section: what keys to expect in the result

### Convention: Artifact tools write to `outputs/`
The `outputs/` directory is gitignored. Artifact files use UTC timestamps in filenames. Agents should call write tools at the end of analysis, not during.

### Convention: Mock data is never modified by tools
Data tools return deep copies of mock data. Analysis tools compute from those copies. Write tools only write to `outputs/`, never to `src/mock_data/`.

---

*Last updated: 2026-03-05 | Covers External Assistant integration commit 23fac21*
