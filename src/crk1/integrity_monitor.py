# CRK-1 Integrity Monitor
# Version 1.0

from __future__ import annotations

from src.crk1.consequence_lattice import (
    ConsequenceExposure,
    apply_amendment_with_drift_check,
    assert_mutation_admissible,
    consequence_exposure,
    mutation_admissible,
    validate_consequence_preservation,
    validate_drift_envelope,
)
from src.crk1.errors import ConstitutionalError
from src.crk1.runtime_facade import CRK1Evidence, CRK1Outcome, CRK1Runtime
from src.crk1.runtime_validator import CRK1RuntimeValidator


class IntegrityMonitor:
    """Real-time drift and insulation detector — the CRK-1 immune system."""

    def __init__(self, runtime: CRK1Runtime, validator: CRK1RuntimeValidator) -> None:
        self.runtime = runtime
        self.validator = validator

    def check_outcome_integrity(self, outcome: CRK1Outcome) -> None:
        if outcome.replayable is not True:
            raise ConstitutionalError("Integrity violation: Outcome not replayable")

    def check_evidence_integrity(self, evidence: CRK1Evidence) -> None:
        if evidence.admissible_for_decision is not True:
            raise ConstitutionalError("Integrity violation: Evidence quarantined")

    def check_lineage_integrity(self, identity_id: str, evidence: CRK1Evidence) -> None:
        lineage = self.runtime.get_lineage(identity_id)
        if evidence.source_identity_id not in lineage:
            raise ConstitutionalError("Integrity violation: lineage escape detected")

    def check_consequence_preservation(self, amendment_changes: dict) -> None:
        """K4 — constitutional change must preserve consequence transmission."""
        validate_consequence_preservation(self.runtime, changes=amendment_changes)

    def check_mutation_admissibility(self, amendment_changes: dict) -> None:
        """K5 — mutation admissibility test."""
        assert_mutation_admissible(amendment_changes)

    def check_drift_envelope(
        self,
        ce_before: ConsequenceExposure,
        ce_after: ConsequenceExposure,
    ) -> None:
        """K6 — CE(S_{t+1}) >= CE(S_t)."""
        validate_drift_envelope(ce_before, ce_after)

    def snapshot_exposure(self) -> ConsequenceExposure:
        return consequence_exposure(self.runtime)

    def check_continuity(self) -> bool:
        """Full system scan for insulation drift."""
        for outcome in self.runtime.get_all_outcomes():
            self.check_outcome_integrity(outcome)

        for evidence in self.runtime.get_all_evidence():
            self.check_evidence_integrity(evidence)

        for identity in self.runtime.get_all_identities():
            admissible_ids = {item.id for item in self.runtime.get_admissible_evidence(identity.id)}
            for evidence in self.runtime.get_all_evidence():
                if evidence.id not in admissible_ids:
                    continue
                self.check_lineage_integrity(identity.id, evidence)

        for amendment in getattr(self.runtime, "_amendments", []):
            self.check_mutation_admissibility(amendment)
            self.check_consequence_preservation(amendment)

        self.runtime._last_consequence_exposure = consequence_exposure(self.runtime)  # noqa: SLF001

        return True
