"""
Semantic search and retrieval for the Program Execution Workbench.

Implements a keyword-based retrieval system using TF-IDF-like scoring
to find contextually relevant memories without requiring external
ML dependencies such as sentence-transformers.

The module is pre-populated with 20 contextual memories covering
similar variance situations, contract precedents, supplier performance
patterns, and common aerospace quality escape root causes.
"""

from __future__ import annotations

import math
import re
from collections import Counter
from datetime import datetime
from typing import Any


# ---------------------------------------------------------------------------
# Pre-populated contextual memories
# ---------------------------------------------------------------------------

_CONTEXTUAL_MEMORIES: list[dict[str, Any]] = [
    # -- Similar variance situations and resolutions --
    {
        "content": (
            "In the AH-64E Block III program (2022), a CPI decline from 0.95 to 0.88 "
            "over 4 months was traced to unplanned rework on the target acquisition "
            "system wiring harness. Resolution involved a dedicated tiger team and "
            "revised manufacturing work instructions, recovering CPI to 0.92 within "
            "2 quarters."
        ),
        "author": "lessons_learned_db",
        "timestamp": "2023-01-15T00:00:00Z",
        "tags": ["precedent", "cpi_decline", "rework", "resolution", "tiger_team"],
        "confidence": 0.9,
        "source": "Lessons Learned Database LL-2023-0045",
    },
    {
        "content": (
            "F-35 Lot 14 experienced SPI degradation to 0.82 when a critical supplier "
            "(landing gear actuators) went on allocation. Recovery required expedited "
            "procurement from a qualified alternate source at 18% cost premium."
        ),
        "author": "lessons_learned_db",
        "timestamp": "2023-03-20T00:00:00Z",
        "tags": ["precedent", "spi_decline", "supply_chain", "alternate_source"],
        "confidence": 0.85,
        "source": "Lessons Learned Database LL-2023-0112",
    },
    {
        "content": (
            "KC-46 program EAC overrun of 12% was primarily attributed to late design "
            "changes in the boom receptacle system. An over-target baseline (OTB) was "
            "eventually established after 3 failed recovery attempts."
        ),
        "author": "lessons_learned_db",
        "timestamp": "2022-11-01T00:00:00Z",
        "tags": ["precedent", "eac_overrun", "design_change", "otb", "rebaseline"],
        "confidence": 0.9,
        "source": "Lessons Learned Database LL-2022-0298",
    },
    {
        "content": (
            "V-22 Osprey nacelle assembly CPI recovered from 0.84 to 0.91 after "
            "implementing lean manufacturing cells and cross-training the workforce. "
            "Key lesson: labor efficiency gains of 15-20% are achievable within "
            "6 months with dedicated process improvement resources."
        ),
        "author": "lessons_learned_db",
        "timestamp": "2023-06-10T00:00:00Z",
        "tags": ["precedent", "cpi_recovery", "lean", "manufacturing", "labor"],
        "confidence": 0.85,
        "source": "Lessons Learned Database LL-2023-0189",
    },
    {
        "content": (
            "When SPI drops below 0.85 for 3 consecutive months without a credible "
            "get-well plan, historical data shows a 78% probability that a formal "
            "schedule rebaseline will eventually be required."
        ),
        "author": "analytics_engine",
        "timestamp": "2024-01-01T00:00:00Z",
        "tags": ["statistical", "spi", "rebaseline", "probability", "threshold"],
        "confidence": 0.8,
        "source": "Program Analytics Historical Model v3.2",
    },
    # -- Contract precedents --
    {
        "content": (
            "On the MQ-25 program, a series of 6 bilateral mods totaling +$12M "
            "triggered a contract type review by DCMA. The review resulted in "
            "additional cost/schedule reporting requirements under DFARS 252.234-7002."
        ),
        "author": "contract_db",
        "timestamp": "2023-08-15T00:00:00Z",
        "tags": ["contract", "modification", "dcma", "dfars", "reporting"],
        "confidence": 0.9,
        "source": "Contract Precedent Database CP-2023-0067",
    },
    {
        "content": (
            "CPIF contracts with cumulative cost overruns exceeding 15% of the target "
            "cost have historically resulted in share-line adjustments during "
            "renegotiation. Average government share increase was 5-8 percentage points."
        ),
        "author": "contract_db",
        "timestamp": "2023-05-01T00:00:00Z",
        "tags": ["contract", "cpif", "overrun", "share_line", "renegotiation"],
        "confidence": 0.85,
        "source": "Contract Precedent Database CP-2023-0041",
    },
    {
        "content": (
            "Nunn-McCurdy unit cost breach thresholds are 15% (significant) and 25% "
            "(critical) above the current APB. Programs exceeding the critical "
            "threshold require OSD recertification to continue."
        ),
        "author": "policy_reference",
        "timestamp": "2024-01-01T00:00:00Z",
        "tags": ["contract", "nunn_mccurdy", "cost_breach", "policy", "threshold"],
        "confidence": 1.0,
        "source": "10 USC 2433 / DoD Instruction 5000.02",
    },
    {
        "content": (
            "Request for Equitable Adjustment (REA) filings have averaged 14 months "
            "to resolution in recent ACAT I programs. Early engagement with the "
            "contracting officer and detailed cost segregation reduce timeline by "
            "approximately 30%."
        ),
        "author": "contract_db",
        "timestamp": "2023-09-01T00:00:00Z",
        "tags": ["contract", "rea", "equitable_adjustment", "timeline"],
        "confidence": 0.8,
        "source": "Contract Precedent Database CP-2023-0088",
    },
    # -- Supplier performance history patterns --
    {
        "content": (
            "Suppliers placed on probation recover to acceptable performance levels "
            "within the 90-day window only 40% of the time. Programs that initiate "
            "alternate source qualification in parallel have lower schedule risk."
        ),
        "author": "analytics_engine",
        "timestamp": "2024-03-01T00:00:00Z",
        "tags": ["supplier", "probation", "recovery_rate", "alternate_source"],
        "confidence": 0.85,
        "source": "Supplier Performance Analytics Model v2.1",
    },
    {
        "content": (
            "DPMO spikes above 3,000 in aerospace fastener suppliers are strongly "
            "correlated (r=0.82) with workforce turnover exceeding 15% annually. "
            "Standard corrective action: require supplier to implement retention "
            "program and increase incoming inspection sampling."
        ),
        "author": "analytics_engine",
        "timestamp": "2024-02-15T00:00:00Z",
        "tags": ["supplier", "dpmo", "fastener", "workforce", "corrective_action"],
        "confidence": 0.8,
        "source": "Supplier Performance Analytics Model v2.1",
    },
    {
        "content": (
            "Sole-source suppliers with delivery ratings below 3.5 have a 65% "
            "probability of causing downstream schedule delays within 2 quarters. "
            "Risk mitigation: safety stock buffer of 4-6 weeks recommended."
        ),
        "author": "analytics_engine",
        "timestamp": "2024-04-01T00:00:00Z",
        "tags": ["supplier", "sole_source", "delivery", "schedule_risk", "buffer"],
        "confidence": 0.8,
        "source": "Supplier Performance Analytics Model v2.1",
    },
    {
        "content": (
            "Composite material suppliers have experienced industrywide lead time "
            "increases of 20-30% since Q3 2023 due to precursor resin shortages. "
            "Programs should plan for 16-20 week lead times versus the historical "
            "12-14 weeks."
        ),
        "author": "industry_intelligence",
        "timestamp": "2024-05-01T00:00:00Z",
        "tags": ["supplier", "composites", "lead_time", "industry", "shortage"],
        "confidence": 0.85,
        "source": "Industry Supply Chain Intelligence Report Q2-2024",
    },
    # -- Common root causes for aerospace quality escapes --
    {
        "content": (
            "Root cause analysis across 150 aerospace quality escapes (2020-2024) shows "
            "the top 5 causes: (1) inadequate work instructions (28%), (2) inspector "
            "workload/fatigue (19%), (3) tooling wear/degradation (16%), (4) material "
            "substitution errors (14%), (5) environmental control failures (11%)."
        ),
        "author": "quality_db",
        "timestamp": "2024-06-01T00:00:00Z",
        "tags": ["quality", "root_cause", "escape", "statistics", "aerospace"],
        "confidence": 0.9,
        "source": "Aerospace Quality Escape Root Cause Study (AIA, 2024)",
    },
    {
        "content": (
            "Torque-related quality escapes in structural assembly are most commonly "
            "caused by: (a) uncalibrated torque tools (42%), (b) incorrect torque "
            "sequence in work order (31%), and (c) operator error/distraction (27%). "
            "Programs implementing digital torque monitoring reduce recurrence by 85%."
        ),
        "author": "quality_db",
        "timestamp": "2024-03-15T00:00:00Z",
        "tags": ["quality", "torque", "root_cause", "structural", "digital_monitoring"],
        "confidence": 0.9,
        "source": "NAVAIR Quality Engineering Best Practices Guide",
    },
    {
        "content": (
            "FOD (Foreign Object Debris) incidents in wing assembly are 3x more likely "
            "during shift changeovers and on overtime shifts. Effective countermeasures "
            "include FOD walks at shift change, tool shadow boards, and zone-based "
            "accountability."
        ),
        "author": "quality_db",
        "timestamp": "2024-04-20T00:00:00Z",
        "tags": ["quality", "fod", "wing_assembly", "shift", "countermeasure"],
        "confidence": 0.9,
        "source": "AS9100 FOD Prevention Handbook",
    },
    {
        "content": (
            "Out-of-tolerance conditions in composite-to-metal interfaces (shimming, "
            "gap filling) account for 22% of all rework hours in modern aircraft "
            "assembly. The primary driver is GD&T stack-up variation combined with "
            "tool wear. Programs using laser scanning for fit-check before final "
            "assembly reduce rework by 60%."
        ),
        "author": "quality_db",
        "timestamp": "2024-05-10T00:00:00Z",
        "tags": ["quality", "composite", "tolerance", "shimming", "rework", "laser"],
        "confidence": 0.85,
        "source": "SAE AIR6296 - Composites Assembly Best Practices",
    },
    {
        "content": (
            "Solder joint reliability failures in avionics LRUs are correlated with "
            "reflow profile deviations exceeding +/- 5C from the validated profile. "
            "IPC-A-610 Class 3 inspection with X-ray sampling catches 92% of latent "
            "defects before delivery."
        ),
        "author": "quality_db",
        "timestamp": "2024-02-01T00:00:00Z",
        "tags": ["quality", "solder", "avionics", "reliability", "inspection"],
        "confidence": 0.9,
        "source": "IPC/JEDEC Joint Reliability Study 2024",
    },
    {
        "content": (
            "Autoclave cure cycle failures in aerospace composites are most often "
            "caused by: thermocouple drift (35%), vacuum bag integrity loss (25%), "
            "resin out-time exceedance (20%), and incorrect layup orientation (15%). "
            "Monthly thermocouple calibration reduces cure failures by 50%."
        ),
        "author": "quality_db",
        "timestamp": "2024-06-15T00:00:00Z",
        "tags": ["quality", "autoclave", "cure", "composites", "thermocouple"],
        "confidence": 0.9,
        "source": "NADCAP Composites Processing Audit Findings Summary",
    },
    {
        "content": (
            "Programs with TCPI above 1.10 that have not established a formal "
            "management reserve drawdown plan recover to budget less than 15% of the "
            "time. The recommended action at TCPI > 1.10 is to initiate EAC "
            "reassessment and engage the customer in a joint review."
        ),
        "author": "analytics_engine",
        "timestamp": "2024-07-01T00:00:00Z",
        "tags": ["evm", "tcpi", "management_reserve", "eac", "recovery"],
        "confidence": 0.85,
        "source": "Program Analytics Historical Model v3.2",
    },
]


# ---------------------------------------------------------------------------
# Tokenization and scoring utilities
# ---------------------------------------------------------------------------

# Common English stop words to exclude from scoring
_STOP_WORDS: set[str] = {
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "is", "it", "as", "was", "are", "be",
    "has", "had", "have", "been", "were", "that", "this", "not", "they",
    "their", "its", "will", "would", "can", "could", "should", "may",
    "more", "than", "also", "all", "any", "each", "which", "when",
    "about", "into", "over", "after", "before", "between", "under",
    "during", "through", "above", "below", "up", "out", "if", "then",
    "so", "no", "only", "very", "just",
}

_TOKEN_PATTERN = re.compile(r"[a-z0-9]+(?:[-_][a-z0-9]+)*")


def _tokenize(text: str) -> list[str]:
    """
    Tokenize text into lowercase terms, excluding stop words.
    Handles hyphenated and underscored compound terms.
    """
    tokens = _TOKEN_PATTERN.findall(text.lower())
    return [t for t in tokens if t not in _STOP_WORDS]


def _compute_idf(corpus: list[list[str]]) -> dict[str, float]:
    """
    Compute inverse document frequency for each term across the corpus.

    IDF(t) = log(N / (1 + df(t)))
    where N = total documents, df(t) = documents containing term t.
    """
    n = len(corpus)
    df: Counter[str] = Counter()
    for doc_tokens in corpus:
        unique_tokens = set(doc_tokens)
        for token in unique_tokens:
            df[token] += 1

    idf: dict[str, float] = {}
    for term, count in df.items():
        idf[term] = math.log(n / (1 + count))

    return idf


def _score_document(
    query_tokens: list[str],
    doc_tokens: list[str],
    tag_tokens: list[str],
    idf: dict[str, float],
) -> float:
    """
    Compute a TF-IDF-like relevance score for a document against a query.

    The score combines:
    - TF-IDF weighted term overlap in document content
    - Tag match bonus (tags are weighted 3x)
    """
    if not query_tokens:
        return 0.0

    doc_tf: Counter[str] = Counter(doc_tokens)
    tag_tf: Counter[str] = Counter(tag_tokens)
    doc_len = max(len(doc_tokens), 1)

    score = 0.0
    for qt in query_tokens:
        term_idf = idf.get(qt, 1.0)

        # Content TF-IDF contribution
        if qt in doc_tf:
            tf = doc_tf[qt] / doc_len
            score += tf * term_idf

        # Tag bonus (weighted higher because tags are curated)
        if qt in tag_tf:
            score += 3.0 * term_idf

    return score


# ---------------------------------------------------------------------------
# MemoryRetriever
# ---------------------------------------------------------------------------

class MemoryRetriever:
    """
    Keyword-based memory retrieval system using TF-IDF-like scoring.

    Provides semantic-like search over a collection of memory records
    without requiring external ML dependencies. The retriever maintains
    a pre-computed IDF index over its corpus and scores queries using
    weighted term frequency and tag matching.

    Parameters
    ----------
    additional_memories : list[dict], optional
        Additional memory records to include alongside the built-in
        contextual memories. Each dict should have at minimum a
        ``content`` key.
    """

    def __init__(
        self,
        additional_memories: list[dict[str, Any]] | None = None,
    ) -> None:
        self._memories: list[dict[str, Any]] = list(_CONTEXTUAL_MEMORIES)
        if additional_memories:
            self._memories.extend(additional_memories)

        # Pre-tokenize corpus and build IDF index
        self._corpus_tokens: list[list[str]] = []
        self._tag_tokens: list[list[str]] = []
        for mem in self._memories:
            content_tokens = _tokenize(mem.get("content", ""))
            self._corpus_tokens.append(content_tokens)
            tag_str = " ".join(mem.get("tags", []))
            self._tag_tokens.append(_tokenize(tag_str))

        # Combine content and tag tokens for IDF computation
        combined = [
            ct + tt
            for ct, tt in zip(self._corpus_tokens, self._tag_tokens)
        ]
        self._idf = _compute_idf(combined)

    @property
    def memory_count(self) -> int:
        """Number of memories in the retriever's corpus."""
        return len(self._memories)

    def add_memory(self, memory: dict[str, Any]) -> None:
        """
        Add a new memory to the corpus and update the index.

        Parameters
        ----------
        memory : dict
            Memory record with at minimum a ``content`` key.
        """
        self._memories.append(memory)
        content_tokens = _tokenize(memory.get("content", ""))
        self._corpus_tokens.append(content_tokens)
        tag_str = " ".join(memory.get("tags", []))
        tag_toks = _tokenize(tag_str)
        self._tag_tokens.append(tag_toks)

        # Rebuild IDF (lightweight for the expected corpus sizes)
        combined = [
            ct + tt
            for ct, tt in zip(self._corpus_tokens, self._tag_tokens)
        ]
        self._idf = _compute_idf(combined)

    def search_similar(
        self,
        query: str,
        memories: list[dict[str, Any]] | None = None,
        top_k: int = 5,
    ) -> list[dict[str, Any]]:
        """
        Search for memories most relevant to the query.

        Uses TF-IDF-weighted keyword matching with tag bonuses to
        rank memories by relevance.

        Parameters
        ----------
        query : str
            Natural-language search query.
        memories : list[dict], optional
            If provided, search this list instead of the internal corpus.
            Each dict must have at minimum a ``content`` key.
        top_k : int
            Maximum number of results to return (default 5).

        Returns
        -------
        list[dict]
            Top-k matching memories, sorted by relevance score descending.
            Each result dict includes an added ``_relevance_score`` key.
        """
        query_tokens = _tokenize(query)
        if not query_tokens:
            return []

        # If an external memory list is provided, score it ad-hoc
        if memories is not None:
            return self._score_external(query_tokens, memories, top_k)

        # Score internal corpus
        scored: list[tuple[float, int]] = []
        for idx in range(len(self._memories)):
            score = _score_document(
                query_tokens,
                self._corpus_tokens[idx],
                self._tag_tokens[idx],
                self._idf,
            )
            if score > 0:
                scored.append((score, idx))

        scored.sort(key=lambda x: x[0], reverse=True)

        results: list[dict[str, Any]] = []
        for score, idx in scored[:top_k]:
            result = dict(self._memories[idx])
            result["_relevance_score"] = round(score, 4)
            results.append(result)

        return results

    def _score_external(
        self,
        query_tokens: list[str],
        memories: list[dict[str, Any]],
        top_k: int,
    ) -> list[dict[str, Any]]:
        """Score and rank an externally provided list of memories."""
        # Tokenize the external corpus
        ext_content: list[list[str]] = []
        ext_tags: list[list[str]] = []
        for mem in memories:
            ext_content.append(_tokenize(mem.get("content", "")))
            tag_str = " ".join(mem.get("tags", []))
            ext_tags.append(_tokenize(tag_str))

        combined = [ct + tt for ct, tt in zip(ext_content, ext_tags)]
        ext_idf = _compute_idf(combined) if combined else {}

        scored: list[tuple[float, int]] = []
        for idx in range(len(memories)):
            score = _score_document(
                query_tokens, ext_content[idx], ext_tags[idx], ext_idf,
            )
            if score > 0:
                scored.append((score, idx))

        scored.sort(key=lambda x: x[0], reverse=True)

        results: list[dict[str, Any]] = []
        for score, idx in scored[:top_k]:
            result = dict(memories[idx])
            result["_relevance_score"] = round(score, 4)
            results.append(result)

        return results

    def get_all_memories(self) -> list[dict[str, Any]]:
        """Return all memories in the corpus."""
        return list(self._memories)
