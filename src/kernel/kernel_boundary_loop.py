"""CRK-T2 runtime outer loop — monitor + controller + governance + ledger."""

from __future__ import annotations

from typing import Any, Protocol

from src.kernel.amendment_controller import KernelAmendmentController
from src.kernel.amendment_ledger import AmendmentStore, KernelAmendmentLedger
from src.kernel.boundary_monitor import KernelBoundaryMonitor
from src.kernel.spine_telemetry import BoundaryTelemetrySource, SpineBoundaryTelemetry


class KernelAmendmentGovernance(Protocol):
    def propose_kernel_amendment(
        self,
        *,
        reason: str,
        signals: list[float],
        insufficiency: float,
        ratify: bool = False,
    ) -> bool: ...

    def current_kernel_version(self) -> int: ...

    def amendment_store(self) -> AmendmentStore: ...


class KernelBoundaryLoop:
    """Outer loop: CRK-T2 boundary control."""

    REASON = "CRK-T2 insufficiency detected"

    def __init__(
        self,
        telemetry: BoundaryTelemetrySource,
        governance: KernelAmendmentGovernance,
        *,
        ledger_store: AmendmentStore | None = None,
    ) -> None:
        self.monitor = KernelBoundaryMonitor(telemetry)
        self.controller = KernelAmendmentController()
        self.governance = governance
        store = ledger_store or governance.amendment_store()
        self.ledger = KernelAmendmentLedger(store=store)
        self.kernel_version = governance.current_kernel_version()

    def snapshot(self) -> dict[str, Any]:
        """Read-only boundary state for cockpit polling (no controller tick)."""
        insuff, raw_i, raw = self.monitor.peek_insufficiency()
        return {
            "amendment_triggered": False,
            "amendment_proposed": self.controller.last_u == 1,
            "amendment_signal": self.controller.last_u,
            "insufficiency": insuff,
            "insufficiency_raw": raw_i,
            "insufficiency_smoothed": insuff,
            "signals": raw.tolist(),
            "kernel_version": self.kernel_version,
            "consecutive_high_epochs": self.controller.high_count,
        }

    def step(self, *, ratify: bool = False) -> dict[str, Any]:
        insuff, raw = self.monitor.compute_insufficiency()
        u = self.controller.decide(insuff)
        signals = raw.tolist()

        if u == 1:
            ratified = self.governance.propose_kernel_amendment(
                reason=self.REASON,
                signals=signals,
                insufficiency=insuff,
                ratify=ratify,
            )
            self.ledger.append(
                kernel_version=self.governance.current_kernel_version(),
                insufficiency=insuff,
                signals=signals,
                reason=self.REASON,
                ratified=bool(ratified),
            )
            if ratified:
                self.kernel_version = self.governance.current_kernel_version()
                self.controller.reset_after_ratification()
            return {
                "amendment_triggered": bool(ratified),
                "amendment_proposed": not ratified,
                "amendment_signal": u,
                "insufficiency": insuff,
                "signals": signals,
                "kernel_version": self.kernel_version,
                "consecutive_high_epochs": self.controller.high_count,
            }

        return {
            "amendment_triggered": False,
            "amendment_proposed": False,
            "amendment_signal": u,
            "insufficiency": insuff,
            "signals": signals,
            "kernel_version": self.kernel_version,
            "consecutive_high_epochs": self.controller.high_count,
        }

    def observe_spine(
        self,
        spine: dict[str, Any],
        *,
        ratify: bool = False,
    ) -> dict[str, Any]:
        self.monitor.telemetry = SpineBoundaryTelemetry(spine=spine)
        return self.step(ratify=ratify)
