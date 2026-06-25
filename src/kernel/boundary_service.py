"""Shared CRK-T2 boundary loop for API and runtime."""

from __future__ import annotations

from src.kernel.governance import Governance
from src.kernel.kernel_boundary_loop import KernelBoundaryLoop
from src.kernel.telemetry import Telemetry

_LOOP: KernelBoundaryLoop | None = None


def get_boundary_loop() -> KernelBoundaryLoop:
    global _LOOP
    if _LOOP is None:
        governance = Governance.current()
        _LOOP = KernelBoundaryLoop(
            Telemetry.current(),
            governance,
            ledger_store=governance.amendment_store(),
        )
        _LOOP.kernel_version = governance.current_kernel_version()
    return _LOOP


def reset_boundary_loop() -> None:
    global _LOOP
    _LOOP = None
    Governance.reset()
    from src.kernel.reference_service import reset_reference_service

    reset_reference_service()
