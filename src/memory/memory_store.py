"""
Memory storage backend for the Program Execution Workbench.

Wraps and extends ADK's InMemoryMemoryService with domain-specific
capabilities including pre-seeded program history facts that provide
historical context for agent analysis.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from google.adk.memory import InMemoryMemoryService


# ---------------------------------------------------------------------------
# Pre-seeded program history facts
# ---------------------------------------------------------------------------

_PROGRAM_HISTORY_FACTS: list[dict[str, Any]] = [
    # -- Past performance trends --
    {
        "category": "performance_trend",
        "content": (
            "CPI has declined steadily from 0.94 to 0.87 over the last 6 months "
            "(Apr 2024: 0.94, May: 0.93, Jun: 0.91, Jul: 0.90, Aug: 0.89, Sep: 0.87), "
            "indicating a persistent and accelerating cost overrun trend."
        ),
        "author": "program_history",
        "tags": ["evm", "cpi", "cost", "trend"],
        "timestamp": "2024-10-01T00:00:00Z",
        "confidence": 1.0,
        "source": "CPR Format 1 Historical Extract",
    },
    {
        "category": "performance_trend",
        "content": (
            "SPI dropped below 1.0 in July 2024 and has remained between 0.86 and 0.89 "
            "since then, correlating with the composite wing skin layup delays."
        ),
        "author": "program_history",
        "tags": ["evm", "spi", "schedule", "trend"],
        "timestamp": "2024-10-01T00:00:00Z",
        "confidence": 1.0,
        "source": "CPR Format 1 Historical Extract",
    },
    {
        "category": "performance_trend",
        "content": (
            "TCPI (BAC-based) has risen from 1.05 to 1.15 over 6 months, "
            "suggesting that recovery to the original budget is increasingly unlikely "
            "without a significant corrective action or rebaseline."
        ),
        "author": "program_history",
        "tags": ["evm", "tcpi", "cost", "forecast"],
        "timestamp": "2024-10-01T00:00:00Z",
        "confidence": 0.95,
        "source": "CPR Format 1 Historical Extract",
    },
    # -- Recurring patterns --
    {
        "category": "recurring_pattern",
        "content": (
            "Wing assembly (WBS 1.3.2) has experienced 3 quality escapes in the last "
            "18 months: (1) incorrect torque values on spar attachment bolts (Mar 2023), "
            "(2) FOD damage during skin panel installation (Sep 2023), and "
            "(3) out-of-tolerance shimming on rib-to-skin interface (Jun 2024). "
            "All three required rework cycles averaging 12 working days each."
        ),
        "author": "program_history",
        "tags": ["quality", "wing_assembly", "rework", "recurring"],
        "timestamp": "2024-10-01T00:00:00Z",
        "confidence": 1.0,
        "source": "Quality Escape Log / FRACAS Database",
    },
    {
        "category": "recurring_pattern",
        "content": (
            "Late engineering change notices (ECNs) have disrupted manufacturing flow "
            "in 4 of the last 6 production lots. The average disruption was 8 working "
            "days per lot, with material scrap costs averaging $145K per occurrence."
        ),
        "author": "program_history",
        "tags": ["engineering", "ecn", "manufacturing", "disruption"],
        "timestamp": "2024-10-01T00:00:00Z",
        "confidence": 0.9,
        "source": "Production Disruption Tracker",
    },
    {
        "category": "recurring_pattern",
        "content": (
            "Composite cure cycle failures have occurred at a rate of roughly 1 in 15 "
            "since the autoclave was recertified in Q1 2024. The root cause is suspected "
            "to be thermocouple drift, but a definitive corrective action is still pending."
        ),
        "author": "program_history",
        "tags": ["manufacturing", "composites", "cure_cycle", "quality"],
        "timestamp": "2024-09-15T00:00:00Z",
        "confidence": 0.85,
        "source": "Manufacturing Engineering Analysis Report",
    },
    # -- Past decisions --
    {
        "category": "past_decision",
        "content": (
            "Dual-sourcing for titanium forgings was evaluated in Q2 2024 but deferred "
            "due to a 14-month qualification timeline for the alternate source (Vulcan "
            "Metals). The decision memo noted that re-evaluation should occur if Apex "
            "Fastener delivery performance drops below 85% OTDP."
        ),
        "author": "program_history",
        "tags": ["supply_chain", "dual_source", "titanium", "decision"],
        "timestamp": "2024-06-30T00:00:00Z",
        "confidence": 1.0,
        "source": "Program Decision Memo PDM-2024-017",
    },
    {
        "category": "past_decision",
        "content": (
            "A schedule rebaseline was proposed in Aug 2024 but rejected by the program "
            "executive officer. The direction was to maintain the current baseline and "
            "report negative variances, with monthly get-well plans required."
        ),
        "author": "program_history",
        "tags": ["schedule", "rebaseline", "decision", "peo"],
        "timestamp": "2024-08-15T00:00:00Z",
        "confidence": 1.0,
        "source": "PEO Direction Memo Aug-2024",
    },
    {
        "category": "past_decision",
        "content": (
            "Overtime authorization was approved for WBS 1.3 (Structures) through "
            "Dec 2024 at up to 20% above baseline labor hours, with estimated cost "
            "impact of $1.2M. Authorization expires end of Q4 2024."
        ),
        "author": "program_history",
        "tags": ["cost", "overtime", "structures", "labor", "decision"],
        "timestamp": "2024-09-01T00:00:00Z",
        "confidence": 1.0,
        "source": "Overtime Authorization OTA-2024-009",
    },
    # -- Contract history --
    {
        "category": "contract_history",
        "content": (
            "4 contract modifications have been executed to date with a total net change "
            "of +$7M to the contract value: P00024 (+$2.1M, GFE integration scope), "
            "P00025 (+$3.5M, revised CDRL requirements), P00026 (+$0.9M, EMI testing "
            "expansion), P00027 (+$0.5M, admin realignment). All were bilateral mods."
        ),
        "author": "program_history",
        "tags": ["contract", "modifications", "cost", "scope"],
        "timestamp": "2024-10-01T00:00:00Z",
        "confidence": 1.0,
        "source": "Contract Administration Office Records",
    },
    {
        "category": "contract_history",
        "content": (
            "A potential 5th modification (P00028) for flight test instrumentation "
            "expansion is under negotiation, with an estimated value of $1.8M. "
            "The government's independent estimate is $1.5M."
        ),
        "author": "program_history",
        "tags": ["contract", "modification", "negotiation", "flight_test"],
        "timestamp": "2024-10-01T00:00:00Z",
        "confidence": 0.9,
        "source": "Contract Administration Status Brief",
    },
    {
        "category": "contract_history",
        "content": (
            "The original contract ceiling is $485M (CPIF). The cumulative contract "
            "mods bring the adjusted ceiling to $492M. Current EAC of $557.5M exceeds "
            "the adjusted ceiling by $65.5M, triggering Nunn-McCurdy review thresholds "
            "if not corrected within 2 reporting periods."
        ),
        "author": "program_history",
        "tags": ["contract", "ceiling", "eac", "nunn_mccurdy", "overrun"],
        "timestamp": "2024-10-01T00:00:00Z",
        "confidence": 0.95,
        "source": "Program Manager's Assessment",
    },
    # -- Supplier history --
    {
        "category": "supplier_history",
        "content": (
            "Apex Fastener was placed on probation in Sep 2024 after OTDP dropped to "
            "72% and DPMO spiked to 4,500. A Supplier Corrective Action Request (SCAR) "
            "was issued (SCAR-2024-031) requiring a 90-day improvement plan. "
            "Failure to meet 85% OTDP by Dec 2024 will trigger disqualification review."
        ),
        "author": "program_history",
        "tags": ["supplier", "apex_fastener", "probation", "quality", "delivery"],
        "timestamp": "2024-09-15T00:00:00Z",
        "confidence": 1.0,
        "source": "Supplier Performance Review Board Minutes",
    },
    {
        "category": "supplier_history",
        "content": (
            "Northwind Composites has maintained >95% OTDP for 12 consecutive months "
            "and was awarded Preferred Supplier status in Q3 2024. However, they have "
            "indicated capacity constraints beyond Lot 8 production quantities."
        ),
        "author": "program_history",
        "tags": ["supplier", "northwind_composites", "performance", "capacity"],
        "timestamp": "2024-10-01T00:00:00Z",
        "confidence": 0.95,
        "source": "Supplier Performance Review Board Minutes",
    },
    {
        "category": "supplier_history",
        "content": (
            "Precision Avionics has 3 open CARs related to solder joint reliability "
            "on the flight management computer. Delivery rating has been declining "
            "(4.2 -> 3.8 -> 3.5 over last 3 quarters). Root cause traced to staffing "
            "turnover in their quality inspection department."
        ),
        "author": "program_history",
        "tags": ["supplier", "precision_avionics", "quality", "corrective_action"],
        "timestamp": "2024-10-01T00:00:00Z",
        "confidence": 0.9,
        "source": "Supplier Performance Dashboard",
    },
]


class WorkbenchMemoryStore:
    """
    Memory storage backend that wraps ADK's InMemoryMemoryService with
    domain-specific capabilities for the Program Execution Workbench.

    On initialization, the store is pre-seeded with program history facts
    covering past performance trends, recurring patterns, past decisions,
    contract history, and supplier history. These facts provide critical
    historical context that agents can query during analysis.
    """

    def __init__(self) -> None:
        self._service = InMemoryMemoryService()
        self._memories: list[dict[str, Any]] = []
        self._preloaded_facts: list[dict[str, Any]] = list(_PROGRAM_HISTORY_FACTS)

        # Pre-seed the memory store with program history facts
        for fact in self._preloaded_facts:
            self._memories.append({
                "content": fact["content"],
                "author": fact["author"],
                "tags": list(fact["tags"]),
                "timestamp": fact.get("timestamp", datetime.utcnow().isoformat()),
                "confidence": fact.get("confidence", 1.0),
                "source": fact.get("source", "program_history"),
                "category": fact.get("category", "general"),
            })

    # -- public properties --

    @property
    def service(self) -> InMemoryMemoryService:
        """Return the underlying ADK memory service for direct access."""
        return self._service

    @property
    def memory_count(self) -> int:
        """Total number of memories (pre-seeded + runtime-added)."""
        return len(self._memories)

    # -- public methods --

    def add_memory(
        self,
        content: str,
        author: str,
        tags: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Add a new memory to the store.

        Parameters
        ----------
        content : str
            The memory content text.
        author : str
            The agent or user that created this memory.
        tags : list[str], optional
            Classification tags for retrieval filtering.

        Returns
        -------
        dict
            The stored memory record.
        """
        memory = {
            "content": content,
            "author": author,
            "tags": tags or [],
            "timestamp": datetime.utcnow().isoformat(),
            "confidence": 0.8,
            "source": f"runtime:{author}",
            "category": "runtime",
        }
        self._memories.append(memory)
        return memory

    async def search(
        self,
        query: str,
        app_name: str,
        user_id: str,
    ) -> Any:
        """
        Search the underlying ADK memory service.

        Delegates to InMemoryMemoryService.search_memory() for semantic
        retrieval. Also performs a local keyword search over pre-seeded
        facts and returns the combined results.

        Parameters
        ----------
        query : str
            Natural-language search query.
        app_name : str
            ADK application name for scoping.
        user_id : str
            ADK user identifier for scoping.

        Returns
        -------
        dict
            Combined search results with keys ``adk_results`` and
            ``local_matches``.
        """
        # Delegate to ADK service
        adk_results = await self._service.search_memory(
            app_name=app_name,
            user_id=user_id,
            query=query,
        )

        # Local keyword search across pre-seeded + runtime memories
        query_lower = query.lower()
        query_terms = set(query_lower.split())

        local_matches: list[dict[str, Any]] = []
        for mem in self._memories:
            content_lower = mem["content"].lower()
            tag_set = {t.lower() for t in mem.get("tags", [])}

            # Score: count of query terms found in content or tags
            content_hits = sum(1 for t in query_terms if t in content_lower)
            tag_hits = sum(1 for t in query_terms if t in tag_set)
            score = content_hits + (tag_hits * 2)  # tags weighted higher

            if score > 0:
                local_matches.append({**mem, "_relevance_score": score})

        # Sort by relevance score descending
        local_matches.sort(key=lambda m: m["_relevance_score"], reverse=True)

        return {
            "adk_results": adk_results,
            "local_matches": local_matches[:10],
        }

    def get_all_memories(self) -> list[dict[str, Any]]:
        """Return all stored memories (pre-seeded and runtime)."""
        return list(self._memories)

    def get_memories_by_category(self, category: str) -> list[dict[str, Any]]:
        """Return memories filtered by category."""
        return [m for m in self._memories if m.get("category") == category]

    def get_memories_by_tag(self, tag: str) -> list[dict[str, Any]]:
        """Return memories that contain the specified tag."""
        tag_lower = tag.lower()
        return [
            m for m in self._memories
            if tag_lower in [t.lower() for t in m.get("tags", [])]
        ]

    def get_preloaded_context(self) -> str:
        """
        Return a formatted string of all pre-seeded program history facts.

        This is intended to be injected into agent prompts as background
        context so that agents are aware of historical patterns and
        decisions before they begin their analysis.

        Returns
        -------
        str
            Multi-section formatted text with all pre-seeded facts.
        """
        sections: dict[str, list[str]] = {
            "performance_trend": [],
            "recurring_pattern": [],
            "past_decision": [],
            "contract_history": [],
            "supplier_history": [],
        }

        for fact in self._preloaded_facts:
            category = fact.get("category", "general")
            if category in sections:
                source_note = f" [Source: {fact['source']}]" if fact.get("source") else ""
                sections[category].append(f"- {fact['content']}{source_note}")

        section_titles = {
            "performance_trend": "PAST PERFORMANCE TRENDS",
            "recurring_pattern": "RECURRING PATTERNS",
            "past_decision": "PAST DECISIONS",
            "contract_history": "CONTRACT HISTORY",
            "supplier_history": "SUPPLIER HISTORY",
        }

        lines: list[str] = [
            "=" * 72,
            "PROGRAM HISTORY CONTEXT (Pre-Loaded Memory)",
            "=" * 72,
            "",
        ]

        for cat_key, title in section_titles.items():
            items = sections.get(cat_key, [])
            if items:
                lines.append(f"--- {title} ---")
                lines.extend(items)
                lines.append("")

        lines.append("=" * 72)
        return "\n".join(lines)
