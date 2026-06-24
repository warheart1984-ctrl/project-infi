"""CRK-1 Red-Team + Drift Stress Suite — unified constitutional attack harness (v1.0)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.crk1.consequence_lattice import consequence_exposure
from src.crk1.drift_simulator import DriftSimulator, is_admissible_drift_result
from src.crk1.errors import ConstitutionalError
from src.crk1.external_reproduction_harness import (
    ExternalReproductionHarness,
    prepare_continuity_substrate,
)
from src.crk1.mission_003_packet import STRESS_BATTERY, verify_packet_artifacts
from src.crk1.runtime_facade import CRK1Decision, CRK1Outcome, CRK1Runtime
from src.crk1.semantic_drift_auditor import SemanticDriftAuditor
from src.crk1.semantic_exposure_monitor import SemanticExposureMonitor


@dataclass
class RedTeamSuiteAttack:
    """Single attack outcome — blocked=True means continuity held."""

    attack_id: str
    attack_class: str
    blocked: bool
    detail: str = ""
    ce_before: float | None = None
    se_before: float | None = None
    ce_after: float | None = None
    se_after: float | None = None


@dataclass
class CRK1RedTeamSuiteReport:
    """Integrated red-team + drift-stress report."""

    attacks: dict[str, bool] = field(default_factory=dict)
    attack_records: list[RedTeamSuiteAttack] = field(default_factory=list)
    drift_results: list[dict[str, Any]] = field(default_factory=list)

    @property
    def attacks_passed(self) -> bool:
        return bool(self.attacks) and all(self.attacks.values())

    @property
    def drift_passed(self) -> bool:
        if not self.drift_results:
            return True
        return all(is_admissible_drift_result(item) for item in self.drift_results)

    @property
    def passed(self) -> bool:
        return self.attacks_passed and self.drift_passed

    def summary(self) -> str:
        lines = ["CRK-1 Red-Team + Drift Stress Suite"]
        for key, ok in sorted(self.attacks.items()):
            lines.append(f"  {key}: {'BLOCKED' if ok else 'FAILED'}")
        drift_ok = sum(1 for item in self.drift_results if is_admissible_drift_result(item))
        lines.append(f"  drift_stress: {drift_ok}/{len(self.drift_results)} admissible")
        lines.append(f"  overall: {'PASS' if self.passed else 'FAIL'}")
        return "\n".join(lines)


class CRK1RedTeamSuite:
    """
    Unified red-team and drift-envelope stress harness.

    If the runtime is correct, every attack returns True (attack blocked).
    If any attack returns False, continuity is broken.
    """

    def __init__(self, runtime: CRK1Runtime, drift_simulator: DriftSimulator | None = None) -> None:
        self.runtime = runtime
        self._monitor = SemanticExposureMonitor(runtime)
        runtime.attach_semantic_monitor(self._monitor)
        self._auditor = SemanticDriftAuditor(runtime, self._monitor)
        self.sim = drift_simulator or DriftSimulator(
            runtime,
            semantic_monitor=self._monitor,
        )

    def _identity_id(self) -> str:
        return self.runtime.kernel.ledgers.identity.id

    def _measure(self) -> tuple[float, float]:
        return consequence_exposure(self.runtime).score, self._monitor.measure_exposure()

    def _seed_outcome(self) -> tuple[str, str]:
        identity = self._identity_id()
        admissible = self.runtime.get_admissible_evidence(identity)
        if not admissible:
            evidence = self.runtime.create_evidence(source_identity_id=identity)
            evidence_ids = [evidence.id]
        else:
            evidence_ids = [admissible[0].id]
        decision = self.runtime.propose_and_execute(identity=identity, evidence=evidence_ids)
        outcomes = self.runtime.get_outcomes(decision.id)
        if not outcomes:
            raise ConstitutionalError("K0: execution must produce outcome")
        return decision.id, outcomes[0].id

    # ============================================================
    # B1 — Mechanical Insulation Attacks (K0–K2)
    # ============================================================

    def attack_drop_outcome(self) -> bool:
        _decision_id, outcome_id = self._seed_outcome()
        try:
            self.runtime.delete_outcome(outcome_id)
            return False
        except ConstitutionalError:
            return True

    def attack_non_replayable_outcome(self) -> bool:
        _decision_id, outcome_id = self._seed_outcome()
        outcome = CRK1Outcome(id=outcome_id, decision_id=_decision_id, replayable=True)
        try:
            outcome.replayable = False
            self.runtime.replay_outcome(outcome_id)
            return False
        except ConstitutionalError:
            return True

    # ============================================================
    # B2 — Structural Insulation Attacks (K3–K6)
    # ============================================================

    def attack_shadow_subsystem(self) -> bool:
        mutation = {
            "target": "constitution",
            "changes": {"block_consequence_propagation": True},
            "justification": "test",
        }
        result = self.sim.test_drift(mutation)
        return is_admissible_drift_result(result) and not result.get("constitutional", False)

    def attack_reduce_exposure(self) -> bool:
        mutation = {
            "target": "constitution",
            "changes": {"insulate_judgment_from_outcomes": True},
            "justification": "reduce CE",
        }
        result = self.sim.test_drift(mutation)
        return is_admissible_drift_result(result) and not result.get("constitutional", False)

    # ============================================================
    # B3 — Semantic Insulation Attacks (K7–K12)
    # ============================================================

    def attack_monoculture(self) -> bool:
        prepare_continuity_substrate(self.runtime)
        frames = self.runtime.get_all_interpretations()
        if not frames:
            return False
        dominant = max(frames, key=lambda frame: frame.weight)
        original = dominant.weight
        try:
            dominant.weight = 1.0
            self._auditor.audit()
            return False
        except ConstitutionalError:
            return True
        finally:
            dominant.weight = original
            self.runtime._semantic._normalize_weights()  # noqa: SLF001

    def attack_remove_adversarial(self) -> bool:
        prepare_continuity_substrate(self.runtime)
        frames = self.runtime.get_all_interpretations()
        originals = {frame.id: frame.adversarial for frame in frames}
        try:
            for frame in frames:
                frame.adversarial = False
            self._auditor.audit()
            return False
        except ConstitutionalError:
            return True
        finally:
            for frame in frames:
                frame.adversarial = originals[frame.id]

    def attack_zero_se(self) -> bool:
        prepare_continuity_substrate(self.runtime)
        frames = self.runtime.get_all_interpretations()
        if not frames:
            return False
        originals = {frame.id: frame.weight for frame in frames}
        try:
            for frame in frames:
                frame.weight = 0.0
            exposure = self._monitor.measure_exposure()
            if exposure <= 0:
                return False
            try:
                self._auditor.audit()
            except ConstitutionalError:
                return True
            return True
        finally:
            for frame in frames:
                frame.weight = originals[frame.id]
            self.runtime._semantic._normalize_weights()  # noqa: SLF001

    # ============================================================
    # B4 — Founder Capture Attacks
    # ============================================================

    def attack_hidden_state(self) -> bool:
        """Founder capture — hidden state must not be required for constitutional operation."""
        setattr(self.runtime, "hidden_founder_state", "secret")
        try:
            ok, _missing = verify_packet_artifacts()
            if not ok:
                return False

            from src.crk1.runtime_validator import DEFAULT_INVARIANTS_PATH
            import yaml

            with DEFAULT_INVARIANTS_PATH.open(encoding="utf-8") as handle:
                doc = yaml.safe_load(handle)
            invs = doc.get("invariants") or {}
            yaml_ok = all(
                key in invs for key in ExternalReproductionHarness.REQUIRED_INVARIANT_KEYS
            )

            identity = self.runtime.kernel.ledgers.identity.id
            hidden = CRK1Decision(
                id="DEC-hidden",
                identity_id=identity,
                evidence_refs=[],
            )
            try:
                self.runtime.save_decision(hidden)
                bypass_ok = False
            except ConstitutionalError:
                bypass_ok = True

            return ok and yaml_ok and bypass_ok
        finally:
            if hasattr(self.runtime, "hidden_founder_state"):
                delattr(self.runtime, "hidden_founder_state")

    # ============================================================
    # Drift Envelope Stress Tests (M3-C)
    # ============================================================

    def drift_stress(self, mutation_set: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
        mutations = mutation_set if mutation_set is not None else list(STRESS_BATTERY)
        return [self.sim.test_drift(mutation) for mutation in mutations]

    # ============================================================
    # Unified Execution
    # ============================================================

    def run_all(self) -> dict[str, bool]:
        """Minimal boolean map — True means attack was blocked."""
        prepare_continuity_substrate(self.runtime)
        return {
            "B1_drop_outcome": self.attack_drop_outcome(),
            "B1_non_replayable": self.attack_non_replayable_outcome(),
            "B2_shadow_subsystem": self.attack_shadow_subsystem(),
            "B2_reduce_exposure": self.attack_reduce_exposure(),
            "B3_monoculture": self.attack_monoculture(),
            "B3_remove_adversarial": self.attack_remove_adversarial(),
            "B3_zero_SE": self.attack_zero_se(),
            "B4_hidden_state": self.attack_hidden_state(),
        }

    def run_full(
        self,
        *,
        mutation_set: list[dict[str, Any]] | None = None,
        include_drift: bool = True,
    ) -> CRK1RedTeamSuiteReport:
        """Integrated report with CE/SE context and drift envelope stress."""
        prepare_continuity_substrate(self.runtime)
        report = CRK1RedTeamSuiteReport()
        ce0, se0 = self._measure()

        attack_specs: list[tuple[str, str, str]] = [
            ("B1", "B1_drop_outcome", "drop_outcome"),
            ("B1", "B1_non_replayable", "non_replayable_outcome"),
            ("B2", "B2_shadow_subsystem", "shadow_subsystem"),
            ("B2", "B2_reduce_exposure", "reduce_exposure"),
            ("B3", "B3_monoculture", "monoculture"),
            ("B3", "B3_remove_adversarial", "remove_adversarial"),
            ("B3", "B3_zero_SE", "zero_SE"),
            ("B4", "B4_hidden_state", "hidden_state"),
        ]
        runners = {
            "drop_outcome": self.attack_drop_outcome,
            "non_replayable_outcome": self.attack_non_replayable_outcome,
            "shadow_subsystem": self.attack_shadow_subsystem,
            "reduce_exposure": self.attack_reduce_exposure,
            "monoculture": self.attack_monoculture,
            "remove_adversarial": self.attack_remove_adversarial,
            "zero_SE": self.attack_zero_se,
            "hidden_state": self.attack_hidden_state,
        }

        for attack_class, attack_id, runner_key in attack_specs:
            blocked = runners[runner_key]()
            ce1, se1 = self._measure()
            report.attacks[attack_id] = blocked
            report.attack_records.append(
                RedTeamSuiteAttack(
                    attack_id=attack_id,
                    attack_class=attack_class,
                    blocked=blocked,
                    ce_before=ce0,
                    se_before=se0,
                    ce_after=ce1,
                    se_after=se1,
                )
            )
            ce0, se0 = ce1, se1

        if include_drift:
            report.drift_results = self.drift_stress(mutation_set)

        return report
