"""
Metrics collection system for the Program Execution Workbench.

Provides a thread-safe, singleton :class:`MetricsCollector` that accumulates
counters, histograms, and gauges for every measurable dimension of the
multi-agent pipeline: tool calls, agent execution time, LLM token usage,
errors, and confidence scores.

Usage:
    from src.observability.metrics import MetricsCollector

    mc = MetricsCollector()          # always returns the same instance
    mc.record_tool_call("pm_agent", "get_milestones", 42.5)
    mc.record_agent_execution("pm_agent", 310.0, token_input=820, token_output=145)
    mc.record_error("risk_agent", "TimeoutError", "LLM call timed out")
    mc.record_confidence("cam_agent", 0.87)

    summary = mc.get_summary()
    mc.export_to_json("metrics_snapshot.json")
"""

import json
import threading
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


class MetricsCollector:
    """Singleton metrics collector for workbench telemetry.

    All public methods are thread-safe.  The singleton is implemented via
    ``__new__`` so that ``MetricsCollector()`` always returns the same
    instance regardless of where it is imported or instantiated.
    """

    _instance: Optional["MetricsCollector"] = None
    _init_lock = threading.Lock()
    _initialized: bool = False

    # -- singleton plumbing -------------------------------------------------

    def __new__(cls) -> "MetricsCollector":
        if cls._instance is None:
            with cls._init_lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        # Guard against re-initialisation on repeated calls to __init__.
        if MetricsCollector._initialized:
            return
        with MetricsCollector._init_lock:
            if MetricsCollector._initialized:
                return
            self._lock = threading.Lock()
            self._start_time = time.monotonic()
            self._start_utc = datetime.now(timezone.utc).isoformat()

            # --- counters / accumulators ---
            # tool_call_count[agent][tool] = int
            self._tool_call_count: Dict[str, Dict[str, int]] = defaultdict(
                lambda: defaultdict(int)
            )
            # tool_call_latency[agent][tool] = [float, ...]
            self._tool_call_latency: Dict[str, Dict[str, List[float]]] = defaultdict(
                lambda: defaultdict(list)
            )
            # agent_execution_time[agent] = [float, ...]
            self._agent_execution_time: Dict[str, List[float]] = defaultdict(list)
            # llm_token_usage[agent] = {"input": int, "output": int}
            self._llm_token_usage: Dict[str, Dict[str, int]] = defaultdict(
                lambda: {"input": 0, "output": 0}
            )
            # error_count[agent][error_type] = int
            self._error_count: Dict[str, Dict[str, int]] = defaultdict(
                lambda: defaultdict(int)
            )
            # error_messages[agent] = [(error_type, message, iso_timestamp), ...]
            self._error_messages: Dict[str, List[tuple]] = defaultdict(list)
            # confidence_scores[agent] = [float, ...]
            self._confidence_scores: Dict[str, List[float]] = defaultdict(list)

            MetricsCollector._initialized = True

    # -- recording methods --------------------------------------------------

    def record_tool_call(
        self, agent: str, tool: str, latency_ms: float
    ) -> None:
        """Record a single tool invocation.

        Parameters
        ----------
        agent:
            Name of the agent that made the call.
        tool:
            Name of the tool that was invoked.
        latency_ms:
            Elapsed wall-clock time in milliseconds.
        """
        with self._lock:
            self._tool_call_count[agent][tool] += 1
            self._tool_call_latency[agent][tool].append(latency_ms)

    def record_agent_execution(
        self,
        agent: str,
        duration_ms: float,
        token_input: int = 0,
        token_output: int = 0,
    ) -> None:
        """Record an agent execution cycle.

        Parameters
        ----------
        agent:
            Name of the executing agent.
        duration_ms:
            Total execution time in milliseconds.
        token_input:
            Number of input (prompt) tokens consumed.
        token_output:
            Number of output (completion) tokens generated.
        """
        with self._lock:
            self._agent_execution_time[agent].append(duration_ms)
            self._llm_token_usage[agent]["input"] += token_input
            self._llm_token_usage[agent]["output"] += token_output

    def record_error(
        self, agent: str, error_type: str, message: str
    ) -> None:
        """Record an error occurrence.

        Parameters
        ----------
        agent:
            Agent where the error occurred.
        error_type:
            Short classification (e.g. ``"ValueError"``, ``"TimeoutError"``).
        message:
            Human-readable description of the error.
        """
        ts = datetime.now(timezone.utc).isoformat()
        with self._lock:
            self._error_count[agent][error_type] += 1
            self._error_messages[agent].append((error_type, message, ts))

    def record_confidence(self, agent: str, score: float) -> None:
        """Record a confidence score emitted by an agent.

        Parameters
        ----------
        agent:
            Agent that produced the score.
        score:
            Confidence value, typically in ``[0, 1]``.
        """
        with self._lock:
            self._confidence_scores[agent].append(score)

    # -- query methods ------------------------------------------------------

    def get_summary(self) -> Dict[str, Any]:
        """Return a snapshot of all collected metrics as a plain dict.

        The returned dictionary is a deep copy; mutating it has no effect
        on the collector's internal state.
        """
        with self._lock:
            return self._build_summary()

    def _build_summary(self) -> Dict[str, Any]:
        """Internal helper (caller must hold ``self._lock``)."""
        elapsed_s = time.monotonic() - self._start_time

        # --- tool calls ---
        tool_calls: Dict[str, Any] = {}
        for agent, tools in self._tool_call_count.items():
            tool_calls[agent] = {}
            for tool, count in tools.items():
                latencies = self._tool_call_latency[agent][tool]
                tool_calls[agent][tool] = {
                    "count": count,
                    "latency_ms": _latency_stats(latencies),
                }

        # --- agent execution ---
        agent_exec: Dict[str, Any] = {}
        for agent, durations in self._agent_execution_time.items():
            agent_exec[agent] = {
                "invocations": len(durations),
                "duration_ms": _latency_stats(durations),
                "tokens": dict(self._llm_token_usage.get(agent, {"input": 0, "output": 0})),
            }

        # --- errors ---
        errors: Dict[str, Any] = {}
        for agent, types in self._error_count.items():
            errors[agent] = {
                "by_type": dict(types),
                "total": sum(types.values()),
                "recent": [
                    {"type": t, "message": m, "timestamp": ts}
                    for t, m, ts in self._error_messages[agent][-10:]
                ],
            }

        # --- confidence ---
        confidence: Dict[str, Any] = {}
        for agent, scores in self._confidence_scores.items():
            confidence[agent] = {
                "count": len(scores),
                "mean": round(sum(scores) / len(scores), 4) if scores else None,
                "min": round(min(scores), 4) if scores else None,
                "max": round(max(scores), 4) if scores else None,
            }

        return {
            "collection_started": self._start_utc,
            "elapsed_seconds": round(elapsed_s, 2),
            "tool_calls": dict(tool_calls),
            "agent_executions": dict(agent_exec),
            "errors": dict(errors),
            "confidence_scores": dict(confidence),
        }

    def export_to_json(self, filepath: str) -> str:
        """Write the current metrics summary to a JSON file.

        Parameters
        ----------
        filepath:
            Destination path.  Parent directories are created if needed.

        Returns
        -------
        str
            The absolute path of the written file.
        """
        dest = Path(filepath).resolve()
        dest.parent.mkdir(parents=True, exist_ok=True)
        summary = self.get_summary()
        with open(str(dest), "w", encoding="utf-8") as fh:
            json.dump(summary, fh, indent=2, default=str)
        return str(dest)

    # -- housekeeping -------------------------------------------------------

    def reset(self) -> None:
        """Clear all accumulated metrics.  Useful in tests."""
        with self._lock:
            self._start_time = time.monotonic()
            self._start_utc = datetime.now(timezone.utc).isoformat()
            self._tool_call_count.clear()
            self._tool_call_latency.clear()
            self._agent_execution_time.clear()
            self._llm_token_usage.clear()
            self._error_count.clear()
            self._error_messages.clear()
            self._confidence_scores.clear()


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _latency_stats(values: List[float]) -> Dict[str, Any]:
    """Compute min / max / mean / p50 / p95 / p99 for a list of latencies."""
    if not values:
        return {"min": None, "max": None, "mean": None, "p50": None, "p95": None, "p99": None}

    sorted_v = sorted(values)
    n = len(sorted_v)

    def _percentile(p: float) -> float:
        idx = (p / 100.0) * (n - 1)
        lo = int(idx)
        hi = min(lo + 1, n - 1)
        frac = idx - lo
        return round(sorted_v[lo] * (1 - frac) + sorted_v[hi] * frac, 2)

    return {
        "min": round(min(sorted_v), 2),
        "max": round(max(sorted_v), 2),
        "mean": round(sum(sorted_v) / n, 2),
        "p50": _percentile(50),
        "p95": _percentile(95),
        "p99": _percentile(99),
    }
