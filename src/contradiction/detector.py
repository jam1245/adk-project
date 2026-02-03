"""
Contradiction detection logic for the Program Execution Workbench.

Implements a rule-based engine that examines agent outputs to identify
conflicting assessments across specialist agents. Seven detection rules
cover the most common contradiction patterns in defense program analysis:

1. CPI/SPI direction disagreement
2. Risk assessment severity conflict
3. Schedule impact mismatch
4. Cost estimate (EAC) divergence
5. Root cause disagreement
6. Mitigation strategy conflict
7. Confidence disparity on same finding type

Each rule produces ``Contradiction`` objects with severity classification
and suggested resolution guidance.
"""

from __future__ import annotations

import re
from typing import Any

from src.state.models import (
    AgentOutput,
    Contradiction,
    ContradictionSeverity,
    Finding,
    FindingType,
)


# ---------------------------------------------------------------------------
# Keyword / pattern helpers
# ---------------------------------------------------------------------------

_IMPROVING_KEYWORDS = {
    "improving", "recovery", "recovering", "positive", "upward",
    "increasing", "better", "gained", "favorable", "trending up",
    "on track", "ahead",
}

_WORSENING_KEYWORDS = {
    "declining", "worsening", "negative", "downward", "decreasing",
    "worse", "degrading", "unfavorable", "trending down", "behind",
    "slipping", "eroding", "deteriorating",
}

_SEVERITY_KEYWORDS: dict[str, set[str]] = {
    "critical": {"critical", "catastrophic", "showstopper", "unacceptable", "severe"},
    "high": {"high", "significant", "major", "serious", "substantial"},
    "medium": {"medium", "moderate", "manageable", "notable"},
    "low": {"low", "minor", "minimal", "negligible", "marginal"},
}

# Pattern to extract numeric durations like "45 days", "6 weeks", "3 months"
_DURATION_PATTERN = re.compile(
    r"(\d+(?:\.\d+)?)\s*(day|days|week|weeks|month|months)",
    re.IGNORECASE,
)

# Pattern to extract dollar amounts like "$557M", "$485,000,000", "$1.2B"
_DOLLAR_PATTERN = re.compile(
    r"\$\s*([\d,]+(?:\.\d+)?)\s*(B|M|K|billion|million|thousand)?",
    re.IGNORECASE,
)

# Pattern to extract percentages
_PERCENT_PATTERN = re.compile(r"(\d+(?:\.\d+)?)\s*%")


def _normalize_dollar(match: re.Match) -> float:
    """Convert a dollar regex match into a float in USD."""
    raw = match.group(1).replace(",", "")
    value = float(raw)
    suffix = (match.group(2) or "").upper()
    multipliers = {"B": 1e9, "BILLION": 1e9, "M": 1e6, "MILLION": 1e6,
                   "K": 1e3, "THOUSAND": 1e3}
    return value * multipliers.get(suffix, 1.0)


def _normalize_duration_to_days(match: re.Match) -> float:
    """Convert a duration regex match to number of days."""
    value = float(match.group(1))
    unit = match.group(2).lower()
    if unit.startswith("week"):
        return value * 7
    if unit.startswith("month"):
        return value * 30
    return value


def _text_lower(finding: Finding) -> str:
    """Return the finding content in lowercase for keyword searches."""
    return finding.content.lower()


def _has_keywords(text: str, keywords: set[str]) -> bool:
    """Check whether any keyword appears in the text."""
    return any(kw in text for kw in keywords)


def _extract_severity_label(text: str) -> str | None:
    """Extract the highest severity keyword found in text."""
    text_lower = text.lower()
    for level in ("critical", "high", "medium", "low"):
        if any(kw in text_lower for kw in _SEVERITY_KEYWORDS[level]):
            return level
    return None


# ---------------------------------------------------------------------------
# ContradictionDetector
# ---------------------------------------------------------------------------

class ContradictionDetector:
    """
    Rule-based engine for detecting contradictions between specialist
    agent outputs in the Program Execution Workbench.

    Usage
    -----
    >>> detector = ContradictionDetector()
    >>> contradictions = detector.detect(workbench_state.agent_outputs)
    >>> classified = detector.classify_severity(contradictions)
    """

    def detect(
        self,
        agent_outputs: dict[str, AgentOutput],
    ) -> list[Contradiction]:
        """
        Run all contradiction detection rules against the agent outputs.

        Parameters
        ----------
        agent_outputs : dict[str, AgentOutput]
            Mapping of agent name to its collected output.

        Returns
        -------
        list[Contradiction]
            All detected contradictions across all rules.
        """
        # Collect all findings across agents
        all_findings: list[Finding] = []
        for output in agent_outputs.values():
            all_findings.extend(output.findings)

        if len(all_findings) < 2:
            return []

        contradictions: list[Contradiction] = []

        # Run each rule
        contradictions.extend(self._rule_cpi_spi_direction(all_findings))
        contradictions.extend(self._rule_risk_severity_conflict(all_findings))
        contradictions.extend(self._rule_schedule_impact_mismatch(all_findings))
        contradictions.extend(self._rule_cost_estimate_divergence(all_findings))
        contradictions.extend(self._rule_root_cause_disagreement(all_findings))
        contradictions.extend(self._rule_mitigation_conflict(all_findings))
        contradictions.extend(self._rule_confidence_disparity(all_findings))

        return contradictions

    # ------------------------------------------------------------------
    # Rule 1: CPI/SPI direction disagreement
    # ------------------------------------------------------------------

    def _rule_cpi_spi_direction(
        self,
        findings: list[Finding],
    ) -> list[Contradiction]:
        """
        Detect when one agent says a performance index (CPI or SPI) is
        improving while another says it is worsening.
        """
        results: list[Contradiction] = []
        evm_terms = {"cpi", "spi", "cost performance", "schedule performance"}

        evm_findings = [
            f for f in findings
            if any(t in _text_lower(f) for t in evm_terms)
        ]

        for i in range(len(evm_findings)):
            for j in range(i + 1, len(evm_findings)):
                if evm_findings[i].agent_name == evm_findings[j].agent_name:
                    continue

                text_a = _text_lower(evm_findings[i])
                text_b = _text_lower(evm_findings[j])

                a_improving = _has_keywords(text_a, _IMPROVING_KEYWORDS)
                a_worsening = _has_keywords(text_a, _WORSENING_KEYWORDS)
                b_improving = _has_keywords(text_b, _IMPROVING_KEYWORDS)
                b_worsening = _has_keywords(text_b, _WORSENING_KEYWORDS)

                if (a_improving and b_worsening) or (a_worsening and b_improving):
                    results.append(Contradiction(
                        finding_a=evm_findings[i],
                        finding_b=evm_findings[j],
                        description=(
                            f"CPI/SPI direction disagreement: "
                            f"'{evm_findings[i].agent_name}' indicates "
                            f"{'improvement' if a_improving else 'decline'} "
                            f"while '{evm_findings[j].agent_name}' indicates "
                            f"{'improvement' if b_improving else 'decline'}."
                        ),
                        severity=ContradictionSeverity.high,
                    ))

        return results

    # ------------------------------------------------------------------
    # Rule 2: Risk assessment severity conflict
    # ------------------------------------------------------------------

    def _rule_risk_severity_conflict(
        self,
        findings: list[Finding],
    ) -> list[Contradiction]:
        """
        Detect when agents assign different severity levels to what
        appears to be the same risk or issue.
        """
        results: list[Contradiction] = []
        risk_terms = {"risk", "threat", "issue", "concern", "hazard"}

        risk_findings = [
            f for f in findings
            if any(t in _text_lower(f) for t in risk_terms)
        ]

        for i in range(len(risk_findings)):
            for j in range(i + 1, len(risk_findings)):
                if risk_findings[i].agent_name == risk_findings[j].agent_name:
                    continue

                sev_a = _extract_severity_label(_text_lower(risk_findings[i]))
                sev_b = _extract_severity_label(_text_lower(risk_findings[j]))

                if sev_a and sev_b and sev_a != sev_b:
                    # Check if findings share subject matter (at least 3 common words)
                    words_a = set(_text_lower(risk_findings[i]).split())
                    words_b = set(_text_lower(risk_findings[j]).split())
                    overlap = words_a & words_b - {"the", "a", "an", "is", "are", "of", "in", "to", "and"}
                    if len(overlap) >= 5:
                        severity_order = ["low", "medium", "high", "critical"]
                        gap = abs(severity_order.index(sev_a) - severity_order.index(sev_b))
                        sev = (
                            ContradictionSeverity.high if gap >= 2
                            else ContradictionSeverity.medium
                        )
                        results.append(Contradiction(
                            finding_a=risk_findings[i],
                            finding_b=risk_findings[j],
                            description=(
                                f"Risk severity conflict: "
                                f"'{risk_findings[i].agent_name}' rates as {sev_a} "
                                f"while '{risk_findings[j].agent_name}' rates as {sev_b}."
                            ),
                            severity=sev,
                        ))

        return results

    # ------------------------------------------------------------------
    # Rule 3: Schedule impact mismatch
    # ------------------------------------------------------------------

    def _rule_schedule_impact_mismatch(
        self,
        findings: list[Finding],
    ) -> list[Contradiction]:
        """
        Detect when different agents report different slip durations
        for what appears to be the same schedule event.
        """
        results: list[Contradiction] = []
        schedule_terms = {"slip", "delay", "behind schedule", "late", "schedule impact"}

        schedule_findings = [
            f for f in findings
            if any(t in _text_lower(f) for t in schedule_terms)
        ]

        for i in range(len(schedule_findings)):
            for j in range(i + 1, len(schedule_findings)):
                if schedule_findings[i].agent_name == schedule_findings[j].agent_name:
                    continue

                text_a = _text_lower(schedule_findings[i])
                text_b = _text_lower(schedule_findings[j])

                durations_a = _DURATION_PATTERN.findall(text_a)
                durations_b = _DURATION_PATTERN.findall(text_b)

                if durations_a and durations_b:
                    days_a = [_normalize_duration_to_days(m) for m in _DURATION_PATTERN.finditer(text_a)]
                    days_b = [_normalize_duration_to_days(m) for m in _DURATION_PATTERN.finditer(text_b)]

                    max_a = max(days_a)
                    max_b = max(days_b)

                    if max_a > 0 and max_b > 0:
                        ratio = max(max_a, max_b) / min(max_a, max_b)
                        if ratio > 1.5:  # More than 50% difference
                            sev = (
                                ContradictionSeverity.high if ratio > 2.0
                                else ContradictionSeverity.medium
                            )
                            results.append(Contradiction(
                                finding_a=schedule_findings[i],
                                finding_b=schedule_findings[j],
                                description=(
                                    f"Schedule impact mismatch: "
                                    f"'{schedule_findings[i].agent_name}' estimates "
                                    f"~{max_a:.0f} days while "
                                    f"'{schedule_findings[j].agent_name}' estimates "
                                    f"~{max_b:.0f} days."
                                ),
                                severity=sev,
                            ))

        return results

    # ------------------------------------------------------------------
    # Rule 4: Cost estimate (EAC) divergence
    # ------------------------------------------------------------------

    def _rule_cost_estimate_divergence(
        self,
        findings: list[Finding],
    ) -> list[Contradiction]:
        """
        Detect when EAC or other cost estimates from different agents
        differ by more than 10%.
        """
        results: list[Contradiction] = []
        cost_terms = {"eac", "estimate at completion", "cost estimate", "projected cost", "total cost"}

        cost_findings = [
            f for f in findings
            if any(t in _text_lower(f) for t in cost_terms)
        ]

        for i in range(len(cost_findings)):
            for j in range(i + 1, len(cost_findings)):
                if cost_findings[i].agent_name == cost_findings[j].agent_name:
                    continue

                text_a = cost_findings[i].content
                text_b = cost_findings[j].content

                dollars_a = [_normalize_dollar(m) for m in _DOLLAR_PATTERN.finditer(text_a)]
                dollars_b = [_normalize_dollar(m) for m in _DOLLAR_PATTERN.finditer(text_b)]

                if dollars_a and dollars_b:
                    # Compare the largest dollar amounts in each finding
                    max_a = max(dollars_a)
                    max_b = max(dollars_b)

                    if max_a > 0 and max_b > 0:
                        pct_diff = abs(max_a - max_b) / min(max_a, max_b)
                        if pct_diff > 0.10:  # More than 10% divergence
                            sev = (
                                ContradictionSeverity.high if pct_diff > 0.25
                                else ContradictionSeverity.medium
                            )
                            results.append(Contradiction(
                                finding_a=cost_findings[i],
                                finding_b=cost_findings[j],
                                description=(
                                    f"Cost estimate divergence ({pct_diff:.0%}): "
                                    f"'{cost_findings[i].agent_name}' cites "
                                    f"${max_a:,.0f} while "
                                    f"'{cost_findings[j].agent_name}' cites "
                                    f"${max_b:,.0f}."
                                ),
                                severity=sev,
                            ))

        return results

    # ------------------------------------------------------------------
    # Rule 5: Root cause disagreement
    # ------------------------------------------------------------------

    def _rule_root_cause_disagreement(
        self,
        findings: list[Finding],
    ) -> list[Contradiction]:
        """
        Detect when agents identify different root causes for what
        appears to be the same issue.
        """
        results: list[Contradiction] = []
        cause_terms = {"root cause", "caused by", "attributed to", "driven by", "due to", "because of"}

        cause_findings = [
            f for f in findings
            if any(t in _text_lower(f) for t in cause_terms)
        ]

        for i in range(len(cause_findings)):
            for j in range(i + 1, len(cause_findings)):
                if cause_findings[i].agent_name == cause_findings[j].agent_name:
                    continue

                text_a = _text_lower(cause_findings[i])
                text_b = _text_lower(cause_findings[j])

                # Check if the findings are discussing the same topic
                # by looking for shared domain keywords (beyond stop words)
                meaningful_words = {
                    "cost", "schedule", "quality", "supplier", "rework",
                    "assembly", "wing", "fastener", "composite", "labor",
                    "material", "delivery", "manufacturing", "tooling",
                    "design", "engineering", "testing", "production",
                    "avionics", "structures", "integration", "software",
                }
                words_a = set(text_a.split()) & meaningful_words
                words_b = set(text_b.split()) & meaningful_words
                shared_topics = words_a & words_b

                if len(shared_topics) >= 2:
                    # Extract the specific cause phrases
                    for term in cause_terms:
                        if term in text_a and term in text_b:
                            # Found same causal language but content differs
                            cause_a_idx = text_a.index(term) + len(term)
                            cause_b_idx = text_b.index(term) + len(term)
                            cause_snippet_a = text_a[cause_a_idx:cause_a_idx + 80].strip()
                            cause_snippet_b = text_b[cause_b_idx:cause_b_idx + 80].strip()

                            if cause_snippet_a != cause_snippet_b:
                                results.append(Contradiction(
                                    finding_a=cause_findings[i],
                                    finding_b=cause_findings[j],
                                    description=(
                                        f"Root cause disagreement on "
                                        f"{', '.join(shared_topics)}: "
                                        f"'{cause_findings[i].agent_name}' vs "
                                        f"'{cause_findings[j].agent_name}' identify "
                                        f"different underlying causes."
                                    ),
                                    severity=ContradictionSeverity.medium,
                                ))
                                break  # One contradiction per finding pair

        return results

    # ------------------------------------------------------------------
    # Rule 6: Mitigation / corrective action conflict
    # ------------------------------------------------------------------

    def _rule_mitigation_conflict(
        self,
        findings: list[Finding],
    ) -> list[Contradiction]:
        """
        Detect when agents recommend conflicting corrective actions or
        mitigation strategies.
        """
        results: list[Contradiction] = []

        # Only look at recommendation and action findings
        rec_findings = [
            f for f in findings
            if f.finding_type in (FindingType.recommendation, FindingType.action)
        ]

        # Define conflicting action pairs
        conflict_pairs: list[tuple[set[str], set[str], str]] = [
            (
                {"accelerate", "expedite", "fast-track", "compress"},
                {"defer", "delay", "postpone", "descope"},
                "schedule approach: acceleration vs. deferral",
            ),
            (
                {"dual-source", "dual source", "alternate source", "second source"},
                {"sole-source", "sole source", "single source", "incumbent"},
                "sourcing strategy: dual-source vs. sole-source",
            ),
            (
                {"increase staffing", "add resources", "augment workforce", "hire", "overtime"},
                {"reduce cost", "cut spending", "reduce headcount", "stop overtime"},
                "resource strategy: increase vs. reduce",
            ),
            (
                {"rebaseline", "reset baseline", "over-target baseline"},
                {"maintain baseline", "hold baseline", "keep baseline", "no rebaseline"},
                "baseline strategy: rebaseline vs. maintain",
            ),
            (
                {"accept risk", "risk acceptance", "accept the risk"},
                {"mitigate risk", "risk mitigation", "reduce risk", "eliminate risk"},
                "risk response: acceptance vs. mitigation",
            ),
        ]

        for i in range(len(rec_findings)):
            for j in range(i + 1, len(rec_findings)):
                if rec_findings[i].agent_name == rec_findings[j].agent_name:
                    continue

                text_a = _text_lower(rec_findings[i])
                text_b = _text_lower(rec_findings[j])

                for set_x, set_y, conflict_desc in conflict_pairs:
                    a_in_x = _has_keywords(text_a, set_x)
                    a_in_y = _has_keywords(text_a, set_y)
                    b_in_x = _has_keywords(text_b, set_x)
                    b_in_y = _has_keywords(text_b, set_y)

                    if (a_in_x and b_in_y) or (a_in_y and b_in_x):
                        results.append(Contradiction(
                            finding_a=rec_findings[i],
                            finding_b=rec_findings[j],
                            description=(
                                f"Mitigation conflict on {conflict_desc}: "
                                f"'{rec_findings[i].agent_name}' vs "
                                f"'{rec_findings[j].agent_name}'."
                            ),
                            severity=ContradictionSeverity.high,
                        ))

        return results

    # ------------------------------------------------------------------
    # Rule 7: Confidence disparity on same finding type
    # ------------------------------------------------------------------

    def _rule_confidence_disparity(
        self,
        findings: list[Finding],
    ) -> list[Contradiction]:
        """
        Detect when two findings of the same type from different agents
        cover similar subject matter but have confidence scores that
        differ by more than 0.3.
        """
        results: list[Contradiction] = []

        for i in range(len(findings)):
            for j in range(i + 1, len(findings)):
                if findings[i].agent_name == findings[j].agent_name:
                    continue

                # Same finding type required
                if findings[i].finding_type != findings[j].finding_type:
                    continue

                # Check confidence gap
                gap = abs(findings[i].confidence - findings[j].confidence)
                if gap <= 0.3:
                    continue

                # Verify topical overlap (at least 4 shared content words)
                words_a = set(_text_lower(findings[i]).split())
                words_b = set(_text_lower(findings[j]).split())
                trivial = {"the", "a", "an", "is", "are", "of", "in", "to", "and", "for", "that", "this", "with"}
                overlap = (words_a & words_b) - trivial
                if len(overlap) >= 4:
                    sev = (
                        ContradictionSeverity.medium if gap <= 0.5
                        else ContradictionSeverity.high
                    )
                    results.append(Contradiction(
                        finding_a=findings[i],
                        finding_b=findings[j],
                        description=(
                            f"Confidence disparity ({gap:.2f}) on "
                            f"{findings[i].finding_type.value} findings: "
                            f"'{findings[i].agent_name}' at {findings[i].confidence:.2f} "
                            f"vs '{findings[j].agent_name}' at {findings[j].confidence:.2f}."
                        ),
                        severity=sev,
                    ))

        return results

    # ------------------------------------------------------------------
    # Severity classification
    # ------------------------------------------------------------------

    def classify_severity(
        self,
        contradictions: list[Contradiction],
    ) -> list[Contradiction]:
        """
        Review and (re-)classify the severity of a list of contradictions
        based on their combined impact.

        Rules:
        - Cost-related contradictions with >25% divergence -> high
        - Schedule contradictions with >2x ratio -> high
        - Multiple contradictions between the same agent pair -> escalate
        - Contradictions involving recommendations/actions -> escalate
        - Otherwise, retain the severity assigned by the detection rule

        Parameters
        ----------
        contradictions : list[Contradiction]
            The contradictions to classify.

        Returns
        -------
        list[Contradiction]
            The same list with potentially updated severity levels.
        """
        if not contradictions:
            return contradictions

        # Count contradictions per agent pair for escalation
        pair_counts: dict[tuple[str, str], int] = {}
        for c in contradictions:
            pair = tuple(sorted([c.finding_a.agent_name, c.finding_b.agent_name]))
            pair_counts[pair] = pair_counts.get(pair, 0) + 1

        for c in contradictions:
            pair = tuple(sorted([c.finding_a.agent_name, c.finding_b.agent_name]))

            # Escalate if multiple contradictions between same pair
            if pair_counts.get(pair, 0) >= 3 and c.severity == ContradictionSeverity.low:
                c.severity = ContradictionSeverity.medium
            elif pair_counts.get(pair, 0) >= 3 and c.severity == ContradictionSeverity.medium:
                c.severity = ContradictionSeverity.high

            # Escalate if findings are recommendations/actions
            if (
                c.finding_a.finding_type in (FindingType.recommendation, FindingType.action)
                and c.finding_b.finding_type in (FindingType.recommendation, FindingType.action)
                and c.severity == ContradictionSeverity.low
            ):
                c.severity = ContradictionSeverity.medium

        return contradictions

    # ------------------------------------------------------------------
    # Resolution suggestion
    # ------------------------------------------------------------------

    def suggest_resolution(self, contradiction: Contradiction) -> str:
        """
        Suggest how to resolve a detected contradiction.

        Generates context-aware resolution guidance based on the
        contradiction type and the agents involved.

        Parameters
        ----------
        contradiction : Contradiction
            The contradiction to generate a resolution for.

        Returns
        -------
        str
            Human-readable resolution suggestion.
        """
        desc_lower = contradiction.description.lower()
        agent_a = contradiction.finding_a.agent_name
        agent_b = contradiction.finding_b.agent_name

        # CPI/SPI direction
        if "cpi" in desc_lower or "spi" in desc_lower or "direction" in desc_lower:
            return (
                f"Resolution: Convene a joint review between {agent_a} and {agent_b} "
                f"to align on the underlying EVM data. Verify that both agents are "
                f"analyzing the same reporting period and WBS scope. If the disagreement "
                f"persists, defer to the CPR Format 1 data as the authoritative source "
                f"and flag the discrepancy for the program manager."
            )

        # Risk severity
        if "risk" in desc_lower and "severity" in desc_lower:
            return (
                f"Resolution: Apply the DoD 5x5 risk matrix consistently. Have {agent_a} "
                f"and {agent_b} independently re-score using the standardized likelihood "
                f"and consequence definitions. If scores still differ, escalate to the "
                f"Risk Review Board for adjudication with documented rationale."
            )

        # Schedule impact
        if "schedule" in desc_lower and ("mismatch" in desc_lower or "impact" in desc_lower):
            return (
                f"Resolution: Cross-reference both estimates against the IMS critical "
                f"path analysis. Validate assumptions about parallel vs. serial task "
                f"execution, resource availability, and dependency logic. The IMS "
                f"network schedule should be the single source of truth for duration "
                f"estimates."
            )

        # Cost divergence
        if "cost" in desc_lower or "eac" in desc_lower or "divergence" in desc_lower:
            return (
                f"Resolution: Reconcile EAC methodologies. Verify whether agents are "
                f"using CPI-based (EAC = BAC/CPI), composite index, or bottom-up "
                f"estimates. Align on a single EAC methodology per program guidance "
                f"and document the basis of estimate. Present all three EAC methods "
                f"in the variance analysis report for leadership visibility."
            )

        # Root cause
        if "root cause" in desc_lower:
            return (
                f"Resolution: Conduct a structured root cause analysis (e.g., Ishikawa "
                f"or 5-Why) with participation from both {agent_a} and {agent_b}. "
                f"Multiple root causes may be valid (contributing factors). Document "
                f"the causal chain and weight each factor's contribution before "
                f"selecting corrective actions."
            )

        # Mitigation conflict
        if "mitigation" in desc_lower or "conflict" in desc_lower:
            return (
                f"Resolution: Evaluate both proposed corrective actions using a "
                f"cost-benefit analysis. Consider whether the actions are truly "
                f"mutually exclusive or can be sequenced (e.g., short-term mitigation "
                f"followed by longer-term strategic change). Present trade-offs to "
                f"the program manager for a decision informed by both perspectives."
            )

        # Confidence disparity
        if "confidence" in desc_lower or "disparity" in desc_lower:
            return (
                f"Resolution: Examine the evidence base underlying each agent's "
                f"confidence level. The agent with lower confidence should identify "
                f"what additional data would increase certainty. Consider whether "
                f"the higher-confidence agent has access to data the other lacks, "
                f"and share information to converge on a justified confidence level."
            )

        # Generic fallback
        return (
            f"Resolution: Schedule a reconciliation review between {agent_a} and "
            f"{agent_b}. Each agent should present its evidence, methodology, and "
            f"assumptions. Identify the root cause of the disagreement and document "
            f"the agreed resolution with supporting rationale."
        )
