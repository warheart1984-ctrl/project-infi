"""ECK-2 unified dual-pipeline kernel."""

from __future__ import annotations

from typing import Any

from datetime import UTC, datetime

from constitutional.eck1.continuity_suite import ECK1ContinuitySuite
from constitutional.eck2.continuity_engine import ECK2ContinuityEngine
from constitutional.eck2.formation_engine import ECK2FormationEngine
from constitutional.eck2.models import ECK2PipelineResult
from constitutional.eck2.reconstruction_engine import ECK2ReconstructionEngine
from constitutional.jpss.invariant_drift import detect_invariant_drift
from constitutional.jpss.invariant_drift_dashboard import InvariantDriftDashboardRuntime
from constitutional.jpss.invariant_register import (
    InvariantEntry,
    load_invariant_register,
    save_invariant_register,
)
from constitutional.jpss.stewardship_balancing_test import (
    StewardshipResponse,
    run_stewardship_balancing_test,
)
from constitutional.runtime.runtime import ConstitutionalStateRuntime


class ECK2Kernel:
    """First dual-pipeline epistemic kernel: JPSS-F + ECK-R."""

    def __init__(self, csr: ConstitutionalStateRuntime) -> None:
        self.csr = csr
        self.formation = ECK2FormationEngine(csr)
        self.reconstruction = ECK2ReconstructionEngine(csr)
        self.continuity = ECK2ContinuityEngine(csr)

    def _resolve_invariant_entry(self, steward_inputs: dict[str, Any]) -> InvariantEntry | None:
        if "invariant_entry" in steward_inputs:
            entry = steward_inputs["invariant_entry"]
            if isinstance(entry, InvariantEntry):
                register = load_invariant_register(self.csr)
                register.append(entry)
                save_invariant_register(self.csr, register)
                return entry

        register = load_invariant_register(self.csr)
        if register.latest() is not None:
            return register.latest()

        defaults = steward_inputs.get("invariant_defaults")
        if not isinstance(defaults, dict):
            return None

        now = datetime.now(UTC).replace(microsecond=0)
        entry = InvariantEntry(
            timestamp=now,
            steward_id=str(steward_inputs.get("steward_id", "steward")),
            purpose_clauses=list(defaults.get("purpose_clauses", [])),
            core_values=list(defaults.get("core_values", [])),
            commitments=list(defaults.get("commitments", [])),
            identity_markers=list(defaults.get("identity_markers", [])),
            sacred_constraints=list(defaults.get("sacred_constraints", [])),
        )
        register.append(entry)
        save_invariant_register(self.csr, register)
        return entry

    def run(self, steward_inputs: dict[str, Any]) -> ECK2PipelineResult:
        formation = self.formation.run(steward_inputs)
        reconstruction = self.reconstruction.reconstruct(formation.decision_id)
        drift_symmetry = self.continuity.compare(formation, reconstruction)
        eck1_suite = ECK1ContinuitySuite(self.csr).run()

        invariant_entry = self._resolve_invariant_entry(steward_inputs)
        invariant_drift = detect_invariant_drift(self.csr, current_invariants=invariant_entry)
        invariant_dashboard = InvariantDriftDashboardRuntime(self.csr).update_snapshot(
            snapshot_at=formation.captured_at
        )

        stewardship_balancing = None
        raw_responses = steward_inputs.get("stewardship_responses")
        if raw_responses:
            responses = [
                item if isinstance(item, StewardshipResponse) else StewardshipResponse(**item)
                for item in raw_responses
            ]
            stewardship_balancing = run_stewardship_balancing_test(
                self.csr,
                str(steward_inputs.get("steward_id", "steward")),
                responses,
            )

        from constitutional.jpss.transferability import evaluate_jpss_transferability

        transferability = evaluate_jpss_transferability(self.csr)

        return ECK2PipelineResult(
            formation=formation,
            reconstruction=reconstruction,
            drift_symmetry=drift_symmetry,
            invariant_drift=invariant_drift,
            invariant_drift_dashboard=invariant_dashboard,
            stewardship_balancing=stewardship_balancing,
            transferability=transferability,
            eck1_continuity=eck1_suite.continuity,
            captured_at=formation.captured_at,
        )


def eck2_from_csr(csr: ConstitutionalStateRuntime) -> ECK2Kernel:
    return ECK2Kernel(csr)
