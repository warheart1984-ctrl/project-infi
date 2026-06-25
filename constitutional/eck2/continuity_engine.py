"""ECK-2 Continuity Engine — drift symmetry between JPSS-F and ECK-R."""

from __future__ import annotations

from datetime import UTC, datetime

from constitutional.eck2.models import DriftSymmetryFinding, DriftSymmetryReport, ECK2ReconstructionResult
from constitutional.jpss.drift import detect_jpss_drift
from constitutional.jpss.models import JPSSCycleResult
from constitutional.runtime.runtime import ConstitutionalStateRuntime


class ECK2ContinuityEngine:
    """Compare forward and reverse cycles for drift symmetry."""

    def __init__(self, csr: ConstitutionalStateRuntime) -> None:
        self.csr = csr

    def compare(
        self,
        formation: JPSSCycleResult,
        reconstruction: ECK2ReconstructionResult,
    ) -> DriftSymmetryReport:
        now = datetime.now(UTC).replace(microsecond=0)
        formation_drift = detect_jpss_drift(self.csr, decision_id=formation.decision_id, cycle=formation)

        layers = [
            ("environment", formation.environment is not None, reconstruction.environment is not None),
            (
                "perception",
                bool(formation.perception.available_signals),
                bool(reconstruction.perception and reconstruction.perception.reconstructable),
            ),
            (
                "salience",
                bool(formation.salience.primary_signals),
                bool(reconstruction.salience and reconstruction.salience.reconstructable),
            ),
            (
                "calibration",
                formation.calibration is not None,
                bool(reconstruction.calibration and reconstruction.calibration.reconstructable),
            ),
            (
                "decision",
                formation.decision is not None,
                bool(reconstruction.judgment and reconstruction.judgment.reconstructable),
            ),
            ("outcome", formation.outcome is not None, "outcome" not in reconstruction.missing_layers),
            ("reflection", formation.reflection is not None, "reflection" not in reconstruction.missing_layers),
            (
                "failure",
                not formation_drift.active_drifts,
                reconstruction.reconstructable,
            ),
        ]

        findings: list[DriftSymmetryFinding] = []
        symmetric_count = 0
        for layer, formation_present, reconstruction_present in layers:
            symmetric = formation_present == reconstruction_present and (
                not formation_present or reconstruction_present
            )
            if symmetric and formation_present:
                symmetric_count += 1
            findings.append(
                DriftSymmetryFinding(
                    layer=layer,
                    formation_present=formation_present,
                    reconstruction_present=reconstruction_present,
                    symmetric=symmetric or (formation_present and reconstruction_present),
                    description="" if symmetric else f"Layer {layer} asymmetric between formation and reconstruction.",
                )
            )

        total = len(layers)
        symmetry_index = symmetric_count / total if total else 0.0
        if reconstruction.reconstructable:
            symmetry_index = max(symmetry_index, 1.0 - (len(reconstruction.missing_layers) / total))

        return DriftSymmetryReport(
            decision_id=formation.decision_id,
            symmetry_index=round(symmetry_index, 4),
            findings=findings,
            formation_drift=formation_drift,
            reconstruction_gaps=reconstruction.missing_layers,
            captured_at=now,
        )
