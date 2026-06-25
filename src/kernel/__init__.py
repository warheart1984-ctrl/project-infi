"""CRK-T2 kernel boundary detection — outer-loop control."""

from src.kernel.amendment_controller import KernelAmendmentController
from src.kernel.amendment_ledger import InMemoryAmendmentStore, KernelAmendmentLedger, KernelAmendmentRecord
from src.kernel.boundary_monitor import DEFAULT_ALPHA, DEFAULT_WEIGHTS, KernelBoundaryMonitor
from src.kernel.governance import Governance
from src.kernel.kernel_boundary_loop import KernelBoundaryLoop
from src.kernel.spine_telemetry import SpineBoundaryTelemetry, telemetry_from_spine
from src.kernel.telemetry import Telemetry

__all__ = [
    "DEFAULT_ALPHA",
    "DEFAULT_WEIGHTS",
    "Governance",
    "InMemoryAmendmentStore",
    "KernelAmendmentController",
    "KernelAmendmentLedger",
    "KernelAmendmentRecord",
    "KernelBoundaryLoop",
    "KernelBoundaryMonitor",
    "SpineBoundaryTelemetry",
    "Telemetry",
    "get_boundary_loop",
    "reset_boundary_loop",
    "telemetry_from_spine",
]


def __getattr__(name: str):
    if name == "ReferenceEvaluator":
        from src.kernel.reference_evaluator import ReferenceEvaluator

        return ReferenceEvaluator
    if name == "get_boundary_loop":
        from src.kernel.boundary_service import get_boundary_loop

        return get_boundary_loop
    if name == "reset_boundary_loop":
        from src.kernel.boundary_service import reset_boundary_loop

        return reset_boundary_loop
    raise AttributeError(name)
