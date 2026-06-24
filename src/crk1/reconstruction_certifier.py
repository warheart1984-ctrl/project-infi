"""Mission #005 Reconstruction Certifier — R-3 Seal."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from src.crk1.governance_reconstruction_receipt import GovernanceReconstructionReceipt
from src.crk1.kernel_challenge_loop import KernelChallengeLoop
from src.crk1.reality_contact_layer import RealitySurfaceRegistry, assert_reality_contact_layer
from src.crk1.reconstruction_operator import reconstruct_or_report
from src.crk1.reconstruction_trace import ReconstructionTrace, as_reconstruction_trace
from src.crk1.judgment_trace import JudgmentTrace


@dataclass
class ReconstructionLevels:
    r1_trace_schema: bool = False
    r2_grr_complete: bool = False
    r3_judgment_reconstructable: bool = False
    r4_reality_contact: bool = False
    r5_kernel_challengeable: bool = False

    @property
    def certified(self) -> bool:
        return all(
            [
                self.r1_trace_schema,
                self.r2_grr_complete,
                self.r3_judgment_reconstructable,
                self.r4_reality_contact,
                self.r5_kernel_challengeable,
            ]
        )


@dataclass
class Mission005CertificationReport:
    mission: str = "005"
    seal: str = "R-3"
    version: str = "1.0"
    levels: ReconstructionLevels = field(default_factory=ReconstructionLevels)
    timestamp: str = ""
    grr_count: int = 0
    trace_count: int = 0
    detail: str = ""

    @property
    def certified(self) -> bool:
        return self.levels.certified

    def to_dict(self) -> dict[str, Any]:
        return {
            "mission": self.mission,
            "seal": self.seal,
            "version": self.version,
            "certified": self.certified,
            "levels": {
                "R1_trace_schema": self.levels.r1_trace_schema,
                "R2_grr_complete": self.levels.r2_grr_complete,
                "R3_judgment_reconstructable": self.levels.r3_judgment_reconstructable,
                "R4_reality_contact": self.levels.r4_reality_contact,
                "R5_kernel_challengeable": self.levels.r5_kernel_challengeable,
            },
            "timestamp": self.timestamp,
            "grr_count": self.grr_count,
            "trace_count": self.trace_count,
            "detail": self.detail,
        }


def _grr_is_complete(grr: GovernanceReconstructionReceipt) -> bool:
    return bool(
        grr.observation.raw_signals
        and grr.interpretation.selected_model
        and grr.commitment.chosen_action
        and grr.binding.decisive_invariants
    )


class Mission005ReconstructionCertifier:
    """Certifies R-3 Seal: non-founder can reconstruct why CRK-1 looks the way it does."""

    def certify(
        self,
        *,
        traces: list[ReconstructionTrace | JudgmentTrace],
        grrs: list[GovernanceReconstructionReceipt],
        reality_registry: RealitySurfaceRegistry | None = None,
        challenge_loop: KernelChallengeLoop | None = None,
        trace_tolerance: float = 0.15,
    ) -> Mission005CertificationReport:
        report = Mission005CertificationReport(
            timestamp=datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
            grr_count=len(grrs),
            trace_count=len(traces),
        )
        levels = ReconstructionLevels()

        levels.r1_trace_schema = len(traces) > 0
        levels.r2_grr_complete = len(grrs) > 0 and all(_grr_is_complete(item) for item in grrs)

        coherent = 0
        for trace in traces:
            normalized = as_reconstruction_trace(trace)
            result = reconstruct_or_report(normalized, tolerance=trace_tolerance)
            if result.coherent:
                coherent += 1
        levels.r3_judgment_reconstructable = len(traces) > 0 and coherent == len(traces)

        if reality_registry is not None:
            try:
                assert_reality_contact_layer(reality_registry)
                levels.r4_reality_contact = True
            except Exception:  # noqa: BLE001
                levels.r4_reality_contact = False
        else:
            levels.r4_reality_contact = False

        loop = challenge_loop or KernelChallengeLoop()
        levels.r5_kernel_challengeable = loop.failure_rate_threshold > 0 and loop.min_samples > 0

        report.levels = levels
        if report.certified:
            report.detail = "R-3 Seal: reconstruction, GRR, reality contact, and kernel challenge path verified."
        else:
            missing = [
                name
                for name, ok in [
                    ("trace_schema", levels.r1_trace_schema),
                    ("grr_complete", levels.r2_grr_complete),
                    ("judgment_reconstructable", levels.r3_judgment_reconstructable),
                    ("reality_contact", levels.r4_reality_contact),
                    ("kernel_challengeable", levels.r5_kernel_challengeable),
                ]
                if not ok
            ]
            report.detail = f"R-3 incomplete — missing: {', '.join(missing)}"
        return report
