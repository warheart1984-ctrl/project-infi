"""Scheduler for constitutional state snapshots — periodic and event-driven."""

from __future__ import annotations

import time
from datetime import UTC, datetime
from typing import Literal

from constitutional.runtime.global_constitutional_state import (
    ConstitutionalStateAggregator,
    GlobalConstitutionalState,
)
from constitutional.runtime.runtime import ConstitutionalStateRuntime

SnapshotTrigger = Literal[
    "boot",
    "interval",
    "transition_threshold",
    "divergence",
    "amendment_ratified",
    "observer_challenge",
    "manual",
]


class ConstitutionalStateScheduler:
    """Triggers constitutional snapshots every N transitions or T minutes, plus on events."""

    def __init__(
        self,
        *,
        transition_threshold: int = 100,
        interval_seconds: float = 300.0,
    ) -> None:
        self.transition_threshold = transition_threshold
        self.interval_seconds = interval_seconds
        self._transition_count = 0
        self._last_tick_monotonic: float | None = None
        self._last_snapshot_at: datetime | None = None

    def should_snapshot_by_time(self) -> bool:
        if self._last_tick_monotonic is None:
            return True
        return (time.monotonic() - self._last_tick_monotonic) >= self.interval_seconds

    def should_snapshot_by_transitions(self) -> bool:
        return self._transition_count >= self.transition_threshold

    def notify_transition(self) -> None:
        self._transition_count += 1

    def reset_transition_counter(self) -> None:
        self._transition_count = 0

    def maybe_snapshot(
        self,
        csr: ConstitutionalStateRuntime,
        *,
        trigger: SnapshotTrigger = "manual",
        force: bool = False,
    ) -> GlobalConstitutionalState | None:
        """Return new snapshot when threshold/time/event warrants it."""
        if not force:
            if trigger == "interval" and not self.should_snapshot_by_time():
                return None
            if trigger == "transition_threshold" and not self.should_snapshot_by_transitions():
                return None
            if trigger not in {
                "boot",
                "divergence",
                "amendment_ratified",
                "observer_challenge",
                "manual",
                "interval",
                "transition_threshold",
            }:
                return None
            if trigger == "interval" and not self.should_snapshot_by_time():
                return None

        aggregator = ConstitutionalStateAggregator(csr)
        state = aggregator.update_snapshot()
        self._last_snapshot_at = state.snapshot_at
        self._last_tick_monotonic = time.monotonic()
        if trigger == "transition_threshold":
            self.reset_transition_counter()
        return state

    def on_divergence(self, csr: ConstitutionalStateRuntime) -> GlobalConstitutionalState:
        return self.maybe_snapshot(csr, trigger="divergence", force=True)  # type: ignore[return-value]

    def on_amendment_ratified(self, csr: ConstitutionalStateRuntime) -> GlobalConstitutionalState:
        return self.maybe_snapshot(csr, trigger="amendment_ratified", force=True)  # type: ignore[return-value]

    def on_observer_challenge(
        self,
        csr: ConstitutionalStateRuntime,
        *,
        opened: bool,
    ) -> GlobalConstitutionalState | None:
        if opened:
            return self.on_divergence(csr)
        return self.maybe_snapshot(csr, trigger="observer_challenge", force=True)

    def tick(self, csr: ConstitutionalStateRuntime) -> GlobalConstitutionalState | None:
        if self.should_snapshot_by_time():
            return self.maybe_snapshot(csr, trigger="interval", force=True)
        if self.should_snapshot_by_transitions():
            return self.maybe_snapshot(csr, trigger="transition_threshold", force=True)
        return None
