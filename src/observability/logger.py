"""
Structured JSON logging system for the Program Execution Workbench.

Provides structured, JSON-formatted log output for all workbench activity
including agent events, tool calls, and system diagnostics. All log entries
carry a trace_id for correlation across the multi-agent execution pipeline.

Usage:
    from src.observability.logger import get_logger, log_tool_call, log_agent_event

    logger = get_logger("pm_agent")
    logger.info("Processing intent", extra_data={"intent": "schedule_review"})

    log_tool_call("pm_agent", "get_milestones", {"program": "AFP"}, result, 42.5, trace_id)
    log_agent_event("pm_agent", "plan_generated", {"steps": 3}, trace_id)
"""

import json
import logging
import os
import sys
import threading
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional


# ---------------------------------------------------------------------------
# Resolve the logs directory relative to the project root.
# Works on Windows and POSIX.  The project root is assumed to be three levels
# above this file: src/observability/logger.py -> project_root
# ---------------------------------------------------------------------------
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_LOGS_DIR = _PROJECT_ROOT / "logs"

# Thread lock for one-time directory creation
_dir_lock = threading.Lock()
_dir_created = False


def _ensure_logs_dir() -> Path:
    """Create the logs/ directory if it does not already exist (thread-safe)."""
    global _dir_created
    if _dir_created:
        return _LOGS_DIR
    with _dir_lock:
        if not _dir_created:
            _LOGS_DIR.mkdir(parents=True, exist_ok=True)
            _dir_created = True
    return _LOGS_DIR


# ---------------------------------------------------------------------------
# JSON Formatter
# ---------------------------------------------------------------------------

class _JsonFormatter(logging.Formatter):
    """Formats each log record as a single-line JSON object."""

    def format(self, record: logging.LogRecord) -> str:
        entry: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "trace_id": getattr(record, "trace_id", None),
            "agent_name": getattr(record, "agent_name", None),
            "message": record.getMessage(),
        }

        # Merge any extra_data attached to the record
        extra_data = getattr(record, "extra_data", None)
        if extra_data is not None:
            entry["extra_data"] = extra_data

        # Capture exception info when present
        if record.exc_info and record.exc_info[1] is not None:
            entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(entry, default=str)


# ---------------------------------------------------------------------------
# WorkbenchLogger
# ---------------------------------------------------------------------------

class WorkbenchLogger:
    """Thin wrapper around :class:`logging.Logger` that injects structured
    fields (trace_id, agent_name, extra_data) into every log record.

    Instances are created via :func:`get_logger`; callers should not
    instantiate this class directly.
    """

    def __init__(self, name: str, level: int = logging.DEBUG) -> None:
        self._logger = logging.getLogger(f"workbench.{name}")
        self._logger.setLevel(level)
        self._logger.propagate = False
        self._name = name

        # Avoid duplicate handlers when get_logger is called multiple times
        # with the same name.
        if not self._logger.handlers:
            self._attach_handlers()

    # -- handler setup ------------------------------------------------------

    def _attach_handlers(self) -> None:
        json_fmt = _JsonFormatter()

        # Console handler (stderr so it does not interfere with stdout data)
        console = logging.StreamHandler(sys.stderr)
        console.setLevel(logging.INFO)
        console.setFormatter(json_fmt)
        self._logger.addHandler(console)

        # File handler
        logs_dir = _ensure_logs_dir()
        log_file = logs_dir / "workbench.log"
        file_handler = logging.FileHandler(str(log_file), encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(json_fmt)
        self._logger.addHandler(file_handler)

    # -- public API ---------------------------------------------------------

    @property
    def name(self) -> str:
        return self._name

    def _log(
        self,
        level: int,
        message: str,
        agent_name: Optional[str] = None,
        trace_id: Optional[str] = None,
        extra_data: Optional[Dict[str, Any]] = None,
    ) -> None:
        extra = {
            "agent_name": agent_name or self._name,
            "trace_id": trace_id,
            "extra_data": extra_data,
        }
        self._logger.log(level, message, extra=extra)

    def debug(
        self,
        message: str,
        agent_name: Optional[str] = None,
        trace_id: Optional[str] = None,
        extra_data: Optional[Dict[str, Any]] = None,
    ) -> None:
        self._log(logging.DEBUG, message, agent_name, trace_id, extra_data)

    def info(
        self,
        message: str,
        agent_name: Optional[str] = None,
        trace_id: Optional[str] = None,
        extra_data: Optional[Dict[str, Any]] = None,
    ) -> None:
        self._log(logging.INFO, message, agent_name, trace_id, extra_data)

    def warning(
        self,
        message: str,
        agent_name: Optional[str] = None,
        trace_id: Optional[str] = None,
        extra_data: Optional[Dict[str, Any]] = None,
    ) -> None:
        self._log(logging.WARNING, message, agent_name, trace_id, extra_data)

    def error(
        self,
        message: str,
        agent_name: Optional[str] = None,
        trace_id: Optional[str] = None,
        extra_data: Optional[Dict[str, Any]] = None,
    ) -> None:
        self._log(logging.ERROR, message, agent_name, trace_id, extra_data)

    def critical(
        self,
        message: str,
        agent_name: Optional[str] = None,
        trace_id: Optional[str] = None,
        extra_data: Optional[Dict[str, Any]] = None,
    ) -> None:
        self._log(logging.CRITICAL, message, agent_name, trace_id, extra_data)


# ---------------------------------------------------------------------------
# Module-level factory & convenience helpers
# ---------------------------------------------------------------------------

# Cache of loggers keyed by name (thread-safe via the GIL for simple dict ops)
_loggers: Dict[str, WorkbenchLogger] = {}
_logger_lock = threading.Lock()


def get_logger(name: str) -> WorkbenchLogger:
    """Return a :class:`WorkbenchLogger` for *name*, creating one if needed.

    Parameters
    ----------
    name:
        Logical name for the logger, typically the agent or subsystem name
        (e.g. ``"pm_agent"``, ``"orchestrator"``).
    """
    if name in _loggers:
        return _loggers[name]
    with _logger_lock:
        # Double-check after acquiring lock
        if name not in _loggers:
            _loggers[name] = WorkbenchLogger(name)
        return _loggers[name]


def log_tool_call(
    agent_name: str,
    tool_name: str,
    params: Optional[Dict[str, Any]],
    result: Any,
    latency_ms: float,
    trace_id: Optional[str] = None,
) -> None:
    """Log a structured record of a tool invocation.

    Parameters
    ----------
    agent_name:
        The agent that invoked the tool.
    tool_name:
        Name of the tool that was called.
    params:
        Parameters passed to the tool.
    result:
        The return value (will be stringified if not JSON-serialisable).
    latency_ms:
        Wall-clock time for the call in milliseconds.
    trace_id:
        Optional correlation id linking this call to a broader trace.
    """
    logger = get_logger(agent_name)
    logger.info(
        f"Tool call: {tool_name}",
        agent_name=agent_name,
        trace_id=trace_id,
        extra_data={
            "event_type": "tool_call",
            "tool_name": tool_name,
            "params": params,
            "result_summary": str(result)[:500],
            "latency_ms": round(latency_ms, 2),
        },
    )


def log_agent_event(
    agent_name: str,
    event_type: str,
    data: Optional[Dict[str, Any]] = None,
    trace_id: Optional[str] = None,
) -> None:
    """Log a structured agent lifecycle or domain event.

    Parameters
    ----------
    agent_name:
        The agent emitting the event.
    event_type:
        Short label such as ``"plan_generated"``, ``"error"``,
        ``"delegation_requested"``.
    data:
        Arbitrary payload for the event.
    trace_id:
        Optional correlation id.
    """
    logger = get_logger(agent_name)
    logger.info(
        f"Agent event: {event_type}",
        agent_name=agent_name,
        trace_id=trace_id,
        extra_data={
            "event_type": event_type,
            **(data or {}),
        },
    )
