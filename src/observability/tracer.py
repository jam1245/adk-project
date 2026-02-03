"""
Distributed-style trace correlation for the Program Execution Workbench.

Provides :class:`TraceContext` value objects, a :class:`Tracer` that manages
the lifecycle of traces and spans, and an :class:`ExecutionReport` that
renders a human-readable summary of a completed trace.

A *trace* represents the full lifecycle of a user intent flowing through the
multi-agent pipeline.  Each agent or sub-operation creates a *span* within
that trace, forming a tree that captures ordering, nesting, and timing.

Usage:
    from src.observability.tracer import Tracer, ExecutionReport

    tracer = Tracer()
    trace_id = tracer.start_trace("Analyse schedule risk for AFP program")

    span_a = tracer.start_span(trace_id, "orchestrator", "triage")
    tracer.end_span(span_a, status="ok")

    span_b = tracer.start_span(trace_id, "risk_agent", "risk_assessment",
                                parent_span_id=span_a)
    tracer.end_span(span_b, status="ok", metadata={"risks_found": 3})

    tracer.end_trace(trace_id, status="completed")

    report = ExecutionReport(tracer.get_trace(trace_id))
    print(report.render())
    tracer.export_trace(trace_id, "traces/my_trace.json")
"""

import json
import threading
import time
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# TraceContext – immutable-ish value object for a single span
# ---------------------------------------------------------------------------

@dataclass
class TraceContext:
    """Represents a single span within a trace.

    Attributes
    ----------
    trace_id : str
        UUID identifying the overall trace.
    span_id : str
        UUID identifying this particular span.
    parent_span_id : str or None
        The span that spawned this one (``None`` for root spans).
    agent_name : str
        Agent or subsystem that owns this span.
    operation : str
        Short label describing the operation (e.g. ``"risk_assessment"``).
    start_time : str
        ISO-8601 timestamp when the span was opened.
    end_time : str or None
        ISO-8601 timestamp when the span was closed.
    status : str
        Terminal status such as ``"ok"``, ``"error"``, ``"timeout"``.
    metadata : dict
        Arbitrary key-value payload attached at span close.
    """

    trace_id: str
    span_id: str
    parent_span_id: Optional[str]
    agent_name: str
    operation: str
    start_time: str
    end_time: Optional[str] = None
    status: str = "in_progress"
    metadata: Dict[str, Any] = field(default_factory=dict)
    _mono_start: float = field(default=0.0, repr=False)

    def duration_ms(self) -> Optional[float]:
        """Return wall-clock duration in milliseconds, or ``None`` if the
        span has not yet been closed."""
        if self.end_time is None:
            return None
        # We stash the monotonic start in _mono_start and compute duration
        # via the monotonic delta recorded at close time.
        return self.metadata.get("_duration_ms")

    def to_dict(self) -> Dict[str, Any]:
        """Serialise to a plain dict (excludes private fields)."""
        d = asdict(self)
        d.pop("_mono_start", None)
        d["duration_ms"] = self.duration_ms()
        return d


# ---------------------------------------------------------------------------
# Trace – container for all spans belonging to one trace
# ---------------------------------------------------------------------------

@dataclass
class _Trace:
    """Internal container grouping spans under a single trace_id."""

    trace_id: str
    intent: str
    start_time: str
    end_time: Optional[str] = None
    status: str = "in_progress"
    spans: Dict[str, TraceContext] = field(default_factory=dict)
    _mono_start: float = field(default=0.0, repr=False)

    def duration_ms(self) -> Optional[float]:
        if self.end_time is None:
            return None
        return self.spans.get("__trace_duration_ms__", None) or None

    def to_dict(self) -> Dict[str, Any]:
        duration = None
        if "__trace_duration_ms__" in self.spans:
            # stored as a sentinel; pop it for export
            pass
        span_list = []
        for sid, ctx in self.spans.items():
            if sid.startswith("__"):
                continue
            span_list.append(ctx.to_dict())

        return {
            "trace_id": self.trace_id,
            "intent": self.intent,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "status": self.status,
            "duration_ms": self._compute_duration(),
            "spans": span_list,
        }

    def _compute_duration(self) -> Optional[float]:
        if self.end_time is None:
            return None
        # Use metadata stashed by Tracer.end_trace
        return self.status  # placeholder replaced below


# ---------------------------------------------------------------------------
# Tracer – manages traces and spans
# ---------------------------------------------------------------------------

class Tracer:
    """Thread-safe trace manager.

    Each call to :meth:`start_trace` creates a new trace (identified by a
    UUID).  Spans are added within a trace via :meth:`start_span` and
    closed with :meth:`end_span`.  When all work is done, call
    :meth:`end_trace` to finalise.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._traces: Dict[str, _Trace] = {}
        self._spans: Dict[str, TraceContext] = {}

    # -- trace lifecycle ----------------------------------------------------

    def start_trace(self, intent: str) -> str:
        """Begin a new trace for *intent* and return the ``trace_id``.

        Parameters
        ----------
        intent:
            Free-text description of the user intent driving this trace.
        """
        trace_id = uuid.uuid4().hex
        now_iso = datetime.now(timezone.utc).isoformat()
        mono = time.monotonic()

        trace = _Trace(
            trace_id=trace_id,
            intent=intent,
            start_time=now_iso,
            _mono_start=mono,
        )

        with self._lock:
            self._traces[trace_id] = trace

        return trace_id

    def end_trace(self, trace_id: str, status: str = "completed") -> None:
        """Finalise a trace.

        Parameters
        ----------
        trace_id:
            The trace to close.
        status:
            Terminal status label (e.g. ``"completed"``, ``"error"``).
        """
        now_iso = datetime.now(timezone.utc).isoformat()
        mono = time.monotonic()

        with self._lock:
            trace = self._traces.get(trace_id)
            if trace is None:
                raise ValueError(f"Unknown trace_id: {trace_id}")
            trace.end_time = now_iso
            trace.status = status
            trace._duration_ms = round((mono - trace._mono_start) * 1000, 2)

    # -- span lifecycle -----------------------------------------------------

    def start_span(
        self,
        trace_id: str,
        agent_name: str,
        operation: str,
        parent_span_id: Optional[str] = None,
    ) -> str:
        """Open a new span inside *trace_id* and return the ``span_id``.

        Parameters
        ----------
        trace_id:
            Must reference a currently open trace.
        agent_name:
            Agent or subsystem that owns the span.
        operation:
            Short label for the work being done.
        parent_span_id:
            Optional parent span for nesting.
        """
        span_id = uuid.uuid4().hex
        now_iso = datetime.now(timezone.utc).isoformat()
        mono = time.monotonic()

        ctx = TraceContext(
            trace_id=trace_id,
            span_id=span_id,
            parent_span_id=parent_span_id,
            agent_name=agent_name,
            operation=operation,
            start_time=now_iso,
            _mono_start=mono,
        )

        with self._lock:
            trace = self._traces.get(trace_id)
            if trace is None:
                raise ValueError(f"Unknown trace_id: {trace_id}")
            trace.spans[span_id] = ctx
            self._spans[span_id] = ctx

        return span_id

    def end_span(
        self,
        span_id: str,
        status: str = "ok",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Close a span.

        Parameters
        ----------
        span_id:
            The span to close.
        status:
            Terminal status (``"ok"``, ``"error"``, etc.).
        metadata:
            Arbitrary data to attach to the span.
        """
        now_iso = datetime.now(timezone.utc).isoformat()
        mono = time.monotonic()

        with self._lock:
            ctx = self._spans.get(span_id)
            if ctx is None:
                raise ValueError(f"Unknown span_id: {span_id}")
            duration_ms = round((mono - ctx._mono_start) * 1000, 2)
            ctx.end_time = now_iso
            ctx.status = status
            ctx.metadata = metadata or {}
            ctx.metadata["_duration_ms"] = duration_ms

    # -- query --------------------------------------------------------------

    def get_trace(self, trace_id: str) -> Dict[str, Any]:
        """Return the full trace tree as a plain dict.

        Parameters
        ----------
        trace_id:
            The trace to retrieve.

        Returns
        -------
        dict
            Serialised trace including all spans.
        """
        with self._lock:
            trace = self._traces.get(trace_id)
            if trace is None:
                raise ValueError(f"Unknown trace_id: {trace_id}")
            return self._serialise_trace(trace)

    def _serialise_trace(self, trace: _Trace) -> Dict[str, Any]:
        """Build the exported dict for a trace (caller must hold lock)."""
        duration_ms: Optional[float] = None
        if hasattr(trace, "_duration_ms"):
            duration_ms = trace._duration_ms

        spans = []
        for sid, ctx in trace.spans.items():
            spans.append(ctx.to_dict())

        # Build a tree structure for nested spans
        span_by_id = {s["span_id"]: s for s in spans}
        roots: List[Dict[str, Any]] = []
        for s in spans:
            s["children"] = []
        for s in spans:
            pid = s.get("parent_span_id")
            if pid and pid in span_by_id:
                span_by_id[pid]["children"].append(s)
            else:
                roots.append(s)

        return {
            "trace_id": trace.trace_id,
            "intent": trace.intent,
            "start_time": trace.start_time,
            "end_time": trace.end_time,
            "status": trace.status,
            "duration_ms": duration_ms,
            "spans": roots,
        }

    # -- export -------------------------------------------------------------

    def export_trace(self, trace_id: str, filepath: str) -> str:
        """Write a trace to a JSON file.

        Parameters
        ----------
        trace_id:
            The trace to export.
        filepath:
            Destination path.  Parent directories are created as needed.

        Returns
        -------
        str
            Absolute path of the written file.
        """
        dest = Path(filepath).resolve()
        dest.parent.mkdir(parents=True, exist_ok=True)
        data = self.get_trace(trace_id)
        with open(str(dest), "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2, default=str)
        return str(dest)

    # -- list / housekeeping ------------------------------------------------

    def list_traces(self) -> List[Dict[str, Any]]:
        """Return summary info for every known trace."""
        with self._lock:
            summaries = []
            for trace in self._traces.values():
                duration_ms = getattr(trace, "_duration_ms", None)
                summaries.append({
                    "trace_id": trace.trace_id,
                    "intent": trace.intent,
                    "status": trace.status,
                    "start_time": trace.start_time,
                    "end_time": trace.end_time,
                    "duration_ms": duration_ms,
                    "span_count": len(trace.spans),
                })
            return summaries


# ---------------------------------------------------------------------------
# ExecutionReport – human-readable rendering of a trace
# ---------------------------------------------------------------------------

class ExecutionReport:
    """Generates a human-readable execution summary from trace data.

    Parameters
    ----------
    trace_data:
        The dict returned by :meth:`Tracer.get_trace`.
    """

    def __init__(self, trace_data: Dict[str, Any]) -> None:
        self._data = trace_data

    def render(self) -> str:
        """Return a formatted, multi-line text report."""
        lines: List[str] = []
        d = self._data

        lines.append("=" * 72)
        lines.append("EXECUTION REPORT")
        lines.append("=" * 72)
        lines.append(f"  Trace ID  : {d['trace_id']}")
        lines.append(f"  Intent    : {d['intent']}")
        lines.append(f"  Status    : {d['status']}")
        lines.append(f"  Started   : {d['start_time']}")
        lines.append(f"  Ended     : {d.get('end_time', 'N/A')}")
        dur = d.get("duration_ms")
        if dur is not None:
            lines.append(f"  Duration  : {dur:.1f} ms")
        lines.append("-" * 72)

        spans = d.get("spans", [])
        if not spans:
            lines.append("  (no spans recorded)")
        else:
            lines.append("  SPAN TREE:")
            lines.append("")
            self._render_spans(spans, lines, indent=2)

        lines.append("=" * 72)

        # Summary statistics
        all_spans = self._flatten_spans(spans)
        agents = sorted(set(s["agent_name"] for s in all_spans))
        lines.append("  SUMMARY")
        lines.append(f"    Total spans : {len(all_spans)}")
        lines.append(f"    Agents      : {', '.join(agents) if agents else 'N/A'}")

        ok_count = sum(1 for s in all_spans if s.get("status") == "ok")
        err_count = sum(1 for s in all_spans if s.get("status") == "error")
        lines.append(f"    OK spans    : {ok_count}")
        lines.append(f"    Error spans : {err_count}")

        durations = [
            s["duration_ms"]
            for s in all_spans
            if s.get("duration_ms") is not None
        ]
        if durations:
            lines.append(f"    Fastest span: {min(durations):.1f} ms")
            lines.append(f"    Slowest span: {max(durations):.1f} ms")

        lines.append("=" * 72)
        return "\n".join(lines)

    # -- internal helpers ---------------------------------------------------

    def _render_spans(
        self,
        spans: List[Dict[str, Any]],
        lines: List[str],
        indent: int,
    ) -> None:
        """Recursively render spans as an indented tree."""
        prefix = " " * indent
        for span in spans:
            dur = span.get("duration_ms")
            dur_str = f"{dur:.1f} ms" if dur is not None else "running"
            status = span.get("status", "unknown")
            status_marker = "[OK]" if status == "ok" else f"[{status.upper()}]"

            lines.append(
                f"{prefix}{status_marker} {span['agent_name']}"
                f" / {span['operation']}"
                f"  ({dur_str})"
            )

            # Show non-private metadata
            meta = {
                k: v
                for k, v in (span.get("metadata") or {}).items()
                if not k.startswith("_")
            }
            if meta:
                for k, v in meta.items():
                    lines.append(f"{prefix}    {k}: {v}")

            children = span.get("children", [])
            if children:
                self._render_spans(children, lines, indent + 4)

    @staticmethod
    def _flatten_spans(spans: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Flatten a nested span tree into a single list."""
        result: List[Dict[str, Any]] = []
        for s in spans:
            result.append(s)
            children = s.get("children", [])
            if children:
                result.extend(ExecutionReport._flatten_spans(children))
        return result
