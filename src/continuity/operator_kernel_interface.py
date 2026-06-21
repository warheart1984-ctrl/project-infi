"""OKI-0001 — Operator-Kernel Interface between humans and the constitutional kernel."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from src.continuity.constitutional_kernel import ConstitutionalKernel, KernelViolation
from src.continuity.creation_operator import SubstrateState
from src.continuity.inheritance import OperatorState
from src.continuity.invariant_engine import DEFAULT_INVARIANT_ENGINE
from src.continuity.lineage import Lineage
from src.continuity.nova_kernel_loop import Event, NovaKernel, fork_lineage, run_kernel_loop
from src.continuity.temporal_governance import TemporalState


OKI_0001_ID = "OKI-0001"
OKI_0001_CAPABILITY_ID = "OKI-0001-operator-kernel-interface"


OKI_0001_CANONICAL_TEXT = """OPERATOR-KERNEL INTERFACE
Codename: OKI-0001
Purpose: API between human operators and the Nova OS Constitutional Kernel.

I. Interface Identity — exposes guarded Create, Evolve, Converge, TemporalSync, Inherit.
II. Core API Methods — every function constitutionally guarded.
III. Operator Feedback — ACCEPTED, REJECTED, REPAIR REQUIRED, TEMPORAL WARNING.
IV. Safety Layer — operators cannot delete continuity, violate invariants, reduce Φ, or corrupt time.
"""


class OperatorFeedback(str, Enum):
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    REPAIR_REQUIRED = "REPAIR_REQUIRED"
    TEMPORAL_WARNING = "TEMPORAL_WARNING"


@dataclass
class OperatorResponse:
    feedback: OperatorFeedback
    detail: str
    payload: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "feedback": self.feedback.value,
            "detail": self.detail,
            "payload": dict(self.payload),
        }


class OperatorKernelInterface:
    """Human-facing gateway to NovaKernel + ConstitutionalKernel."""

    def __init__(
        self,
        *,
        kernel: NovaKernel | None = None,
        constitutional_kernel: ConstitutionalKernel | None = None,
    ) -> None:
        self.kernel = kernel or NovaKernel()
        self.constitutional_kernel = constitutional_kernel or ConstitutionalKernel()
        self.invariants = DEFAULT_INVARIANT_ENGINE

    def create(self, event: Event) -> OperatorResponse:
        try:
            result = run_kernel_loop(event, self.kernel)
            if result.status != "ok":
                return OperatorResponse(
                    OperatorFeedback.REJECTED,
                    "; ".join(result.errors) or "kernel loop rejected event",
                    result.to_dict(),
                )
            return OperatorResponse(OperatorFeedback.ACCEPTED, "lawful creation recorded", result.to_dict())
        except Exception as exc:
            return OperatorResponse(OperatorFeedback.REJECTED, str(exc), {})

    def evolve(
        self,
        before: SubstrateState,
        after: SubstrateState,
        active_lineages: list[Lineage],
    ) -> OperatorResponse:
        enforcement = self.invariants.enforce_or_reject(before.lineage, after.lineage)
        if enforcement["action"] != "accept":
            return OperatorResponse(
                OperatorFeedback.REPAIR_REQUIRED,
                "invariant engine rejected evolution",
                enforcement,
            )
        try:
            payload = self.constitutional_kernel.evolve(before, after, active_lineages)
            return OperatorResponse(OperatorFeedback.ACCEPTED, "lawful evolution", payload)
        except KernelViolation as exc:
            return OperatorResponse(OperatorFeedback.REJECTED, str(exc), {})

    def converge(self, lineages: list[Lineage]) -> OperatorResponse:
        try:
            payload = self.constitutional_kernel.converge(lineages)
            from src.continuity.convergence_algebra import converge_many

            merged, _ = converge_many(lineages)
            propagation = self.invariants.propagate_convergence(lineages, merged)
            if not propagation["passed"]:
                return OperatorResponse(
                    OperatorFeedback.REPAIR_REQUIRED,
                    "convergence invariant propagation failed",
                    propagation,
                )
            return OperatorResponse(OperatorFeedback.ACCEPTED, "lineages reconciled", payload)
        except KernelViolation as exc:
            return OperatorResponse(OperatorFeedback.REPAIR_REQUIRED, str(exc), {})

    def temporal_sync(self, past: TemporalState, future: TemporalState) -> OperatorResponse:
        try:
            payload = self.constitutional_kernel.temporal_sync(past, future)
            feedback = OperatorFeedback.ACCEPTED
            detail = "temporal coherence preserved"
            if float(payload["coherence"].get("phi_t1_t2", 1.0)) < self.kernel.phi_min:
                feedback = OperatorFeedback.TEMPORAL_WARNING
                detail = "temporal coherence risk — Φ near threshold"
            return OperatorResponse(feedback, detail, payload)
        except KernelViolation as exc:
            return OperatorResponse(OperatorFeedback.REJECTED, str(exc), {})

    def inherit(
        self,
        predecessor: OperatorState,
        successor: OperatorState,
        civilization_lineages: list[Lineage],
    ) -> OperatorResponse:
        try:
            payload = self.constitutional_kernel.inherit(predecessor, successor, civilization_lineages)
            return OperatorResponse(OperatorFeedback.ACCEPTED, "continuity inherited", payload)
        except KernelViolation as exc:
            return OperatorResponse(OperatorFeedback.REJECTED, str(exc), {})

    def fork(self, source_id: str, new_id: str, reason: str) -> OperatorResponse:
        try:
            record = fork_lineage(self.kernel, source_id, new_id, reason)
            return OperatorResponse(
                OperatorFeedback.ACCEPTED,
                "lineage forked with invariant preservation",
                record.to_dict(),
            )
        except Exception as exc:
            return OperatorResponse(OperatorFeedback.REJECTED, str(exc), {})


def run_operator_kernel_interface_proof() -> dict[str, Any]:
    oki = OperatorKernelInterface()
    genesis = oki.create(
        Event(
            event_id="EVT-OKI-0001",
            kind="creation.intent",
            actor="OPERATOR:JON",
            lineage="L0-GENESIS",
            timestamp="2026-01-01T00:00:00Z",
            payload={"kind": "oki.proof"},
        )
    )
    fork = oki.fork("L0-GENESIS", "L1-OPERATOR-WORKSPACE", "operator workspace")
    passed = genesis.feedback == OperatorFeedback.ACCEPTED and fork.feedback == OperatorFeedback.ACCEPTED
    return {
        "capability_id": OKI_0001_CAPABILITY_ID,
        "create": genesis.to_dict(),
        "fork": fork.to_dict(),
        "passed": passed,
    }
