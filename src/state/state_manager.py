"""
State persistence and versioning for the Program Execution Workbench.

Provides a StateManager that maintains a versioned history of
WorkbenchState snapshots, supporting rollback, agent output updates,
and status transitions throughout the multi-agent analysis lifecycle.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime
from typing import Optional

from src.state.models import (
    AgentOutput,
    WorkbenchState,
    WorkbenchStatus,
)


class StateManager:
    """
    Manages versioned snapshots of the WorkbenchState.

    Every call to ``save_state`` creates a new immutable snapshot.
    Previous versions can be retrieved or rolled back to at any time.
    Helper methods are provided to apply common mutations (adding agent
    output, changing pipeline status) and automatically persist the
    resulting state.

    Attributes
    ----------
    _history : list[tuple[int, datetime, WorkbenchState]]
        Internal version history.  Each entry is
        ``(version_number, timestamp, state_snapshot)``.
    """

    def __init__(self) -> None:
        self._history: list[tuple[int, datetime, WorkbenchState]] = []
        self._next_version: int = 1

    # ------------------------------------------------------------------
    # Core versioning operations
    # ------------------------------------------------------------------

    def save_state(self, state: WorkbenchState) -> int:
        """
        Persist a deep-copy snapshot of the given state.

        Parameters
        ----------
        state : WorkbenchState
            The state to snapshot.

        Returns
        -------
        int
            The version number assigned to this snapshot.
        """
        version = self._next_version
        self._next_version += 1
        snapshot = deepcopy(state)
        self._history.append((version, datetime.utcnow(), snapshot))
        return version

    def get_state(self, version: int = -1) -> WorkbenchState:
        """
        Retrieve a state snapshot by version number.

        Parameters
        ----------
        version : int, optional
            The version to retrieve.  Use ``-1`` (the default) to get
            the most recent snapshot.

        Returns
        -------
        WorkbenchState
            A deep copy of the requested snapshot.

        Raises
        ------
        ValueError
            If no snapshots exist or the requested version is not found.
        """
        if not self._history:
            raise ValueError("No state snapshots have been saved yet.")

        if version == -1:
            return deepcopy(self._history[-1][2])

        for v, _ts, snap in self._history:
            if v == version:
                return deepcopy(snap)

        available = [v for v, _, _ in self._history]
        raise ValueError(
            f"Version {version} not found.  Available versions: {available}"
        )

    def get_state_history(self) -> list[tuple[int, datetime, str]]:
        """
        Return a summary of all saved snapshots.

        Returns
        -------
        list[tuple[int, datetime, str]]
            Each tuple contains ``(version_number, timestamp,
            workbench_status_value)``.
        """
        return [
            (v, ts, snap.status.value)
            for v, ts, snap in self._history
        ]

    def rollback(self, version: int) -> WorkbenchState:
        """
        Roll back to a previous version.

        This retrieves the snapshot at the given version and saves it
        as a *new* version (the history is append-only, so no data is
        lost).

        Parameters
        ----------
        version : int
            The version number to roll back to.

        Returns
        -------
        WorkbenchState
            A deep copy of the rolled-back state (which is also the
            new latest version).

        Raises
        ------
        ValueError
            If the requested version does not exist.
        """
        target_state = self.get_state(version)
        self.save_state(target_state)
        return deepcopy(target_state)

    # ------------------------------------------------------------------
    # Convenience mutation helpers
    # ------------------------------------------------------------------

    def update_agent_output(
        self,
        state: WorkbenchState,
        agent_name: str,
        output: AgentOutput,
    ) -> WorkbenchState:
        """
        Add or replace an agent's output in the state.

        Parameters
        ----------
        state : WorkbenchState
            The current state to update.
        agent_name : str
            Name of the agent whose output is being recorded.
        output : AgentOutput
            The agent's output payload.

        Returns
        -------
        WorkbenchState
            A new state instance with the agent output applied.
            The caller should save this via ``save_state`` if desired.
        """
        updated = deepcopy(state)
        updated.agent_outputs[agent_name] = output
        return updated

    def update_status(
        self,
        state: WorkbenchState,
        new_status: WorkbenchStatus,
    ) -> WorkbenchState:
        """
        Transition the workbench to a new pipeline status.

        Parameters
        ----------
        state : WorkbenchState
            The current state to update.
        new_status : WorkbenchStatus
            The new pipeline stage.

        Returns
        -------
        WorkbenchState
            A new state instance with the updated status.
        """
        updated = deepcopy(state)
        updated.status = new_status
        return updated

    # ------------------------------------------------------------------
    # Informational helpers
    # ------------------------------------------------------------------

    @property
    def latest_version(self) -> Optional[int]:
        """Return the most recent version number, or None if empty."""
        if not self._history:
            return None
        return self._history[-1][0]

    @property
    def version_count(self) -> int:
        """Total number of saved snapshots."""
        return len(self._history)

    def has_state(self) -> bool:
        """Return True if at least one snapshot has been saved."""
        return len(self._history) > 0
