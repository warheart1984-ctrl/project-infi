"""CRK-1 Red-Team Protocol — Mission #003 Part II."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Literal

from src.crk1.attack_simulator import InsulationAttackSimulator
from src.crk1.consequence_lattice import apply_amendment_with_drift_check, consequence_exposure
from src.crk1.mission_003_packet import verify_packet_artifacts
from src.crk1.drift_simulator import DriftSimulator, is_admissible_drift_result
from src.crk1.errors import ConstitutionalError
from src.crk1.external_reproduction_harness import prepare_continuity_substrate
from src.crk1.semantic_reproduction_harness import SemanticReproductionHarness
from src.crk1.runtime_facade import CRK1Decision
from src.crk1.semantic_drift_auditor import SemanticDriftAuditor
from src.crk1.semantic_exposure_monitor import SemanticExposureMonitor

if TYPE_CHECKING:
    from src.crk1.runtime_facade import CRK1Runtime

AttackStatus = Literal["PASS", "FAILED", "REJECTED"]


@dataclass
class RedTeamAttackResult:
    attack_class: str
    attack_id: str
    name: str
    status: AttackStatus
    detail: str = ""
    ce_before: float | None = None
    se_before: float | None = None
    ce_after: float | None = None
    se_after: float | None = None


@dataclass
class RedTeamReport:
    attacks: list[RedTeamAttackResult] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return all(attack.status in ("PASS", "REJECTED") for attack in self.attacks)

    @property
    def failures(self) -> list[RedTeamAttackResult]:
        return [attack for attack in self.attacks if attack.status == "FAILED"]

    def summary(self) -> str:
        lines = ["CRK-1 Red-Team Protocol"]
        for attack in self.attacks:
            lines.append(f"  [{attack.status}] {attack.attack_class}/{attack.attack_id}: {attack.name}")
            if attack.detail:
                lines.append(f"           {attack.detail}")
        lines.append(f"Overall: {'PASS' if self.passed else 'FAIL'}")
        return "\n".join(lines)


class RedTeamProtocol:
    """Adversarial assault on CRK-1 — mechanical, structural, semantic, founder capture."""

    def __init__(self, runtime: CRK1Runtime) -> None:
        self.runtime = runtime
        self.mechanical = InsulationAttackSimulator(runtime)
        self.drift = DriftSimulator(runtime, semantic_monitor=SemanticExposureMonitor(runtime))
        self.semantic_auditor = SemanticDriftAuditor(runtime, SemanticExposureMonitor(runtime))

    def _measure_exposure(self) -> tuple[float, float]:
        ce = consequence_exposure(self.runtime).score
        se = SemanticExposureMonitor(self.runtime).measure_exposure()
        return ce, se

    def _record(
        self,
        attack_class: str,
        attack_id: str,
        name: str,
        status: AttackStatus,
        detail: str = "",
        *,
        ce_before: float | None = None,
        se_before: float | None = None,
        ce_after: float | None = None,
        se_after: float | None = None,
    ) -> RedTeamAttackResult:
        return RedTeamAttackResult(
            attack_class,
            attack_id,
            name,
            status,
            detail,
            ce_before=ce_before,
            se_before=se_before,
            ce_after=ce_after,
            se_after=se_after,
        )

    def run_class_b1_mechanical(self, identity: str) -> list[RedTeamAttackResult]:
        ce0, se0 = self._measure_exposure()
        report = self.mechanical.run_all(identity)
        ce1, se1 = self._measure_exposure()
        results: list[RedTeamAttackResult] = []
        labels = {
            "drop_outcome": ("B1-01", "Drop Outcomes before Evidence"),
            "non_replayable_outcome": ("B1-02", "Create non-replayable Outcomes"),
            "quarantine_evidence": ("B1-03", "Bypass EvidenceContract (quarantine)"),
            "fork_without_history": ("B1-04", "Lineage escape"),
            "decision_without_evidence": ("B1-05", "Decision without evidence"),
            "replay_bypass": ("B1-06", "Replay bypass"),
        }
        for key, (_ignored, outcome) in report.items():
            attack_id, name = labels.get(key, (key, key))
            status: AttackStatus = "PASS" if outcome == "PASS" else "FAILED"
            results.append(
                self._record(
                    "B1",
                    attack_id,
                    name,
                    status,
                    outcome,
                    ce_before=ce0,
                    se_before=se0,
                    ce_after=ce1,
                    se_after=se1,
                )
            )
        return results

    def run_class_a_mechanical(self, identity: str) -> list[RedTeamAttackResult]:
        return self.run_class_b1_mechanical(identity)

    def run_class_b2_structural(self, identity: str) -> list[RedTeamAttackResult]:
        results: list[RedTeamAttackResult] = []
        ce0, se0 = self._measure_exposure()

        insulating = self.drift.test_drift(
            {"target": "constitution", "changes": {"Outcome.replayable": False}},
        )
        results.append(
            self._record(
                "B2",
                "B2-01",
                "Shadow Outcome path (disable replayability)",
                "REJECTED"
                if is_admissible_drift_result(insulating) and not insulating.get("constitutional")
                else "FAILED",
                ce_before=ce0,
                se_before=se0,
            )
        )

        ce_mid, se_mid = self._measure_exposure()
        try:
            evidence = self.runtime.create_evidence()
            self.runtime.mark_evidence_non_admissible(evidence.id)
            results.append(
                self._record("B2", "B2-02", "Policy non-admissible Evidence", "FAILED")
            )
        except ConstitutionalError:
            results.append(
                self._record(
                    "B2",
                    "B2-02",
                    "Policy non-admissible Evidence",
                    "REJECTED",
                    ce_before=ce_mid,
                    se_before=se_mid,
                )
            )

        block = self.drift.test_drift(
            {"target": "constitution", "changes": {"block_consequence_propagation": True}},
        )
        results.append(
            self._record(
                "B2",
                "B2-03",
                "Block consequence propagation",
                "REJECTED" if is_admissible_drift_result(block) and not block.get("constitutional") else "FAILED",
            )
        )

        try:
            apply_amendment_with_drift_check(
                self.runtime,
                {"insulate_judgment_from_outcomes": True},
            )
            results.append(
                self._record("B2", "B2-04", "Governance bypass (direct amendment)", "FAILED")
            )
        except ConstitutionalError:
            results.append(
                self._record("B2", "B2-04", "Governance bypass (direct amendment)", "REJECTED")
            )

        try:
            from src.crk1.governance_engine import GovernanceEngine
            from src.crk1.runtime_validator import CRK1RuntimeValidator

            engine = GovernanceEngine(self.runtime, CRK1RuntimeValidator())
            engine.propose(
                identity,
                {
                    "type": "amendment",
                    "content": {"insulate_judgment_from_outcomes": True},
                    "justification": "shadow governance",
                    "evidence_ids": [],
                },
            )
            results.append(self._record("B2", "B2-05", "Governance without evidence", "FAILED"))
        except ConstitutionalError:
            results.append(
                self._record("B2", "B2-05", "Governance without evidence", "REJECTED")
            )

        shadow = self.runtime._disable_outcome_creation  # noqa: SLF001
        try:
            self.runtime._disable_outcome_creation = True  # noqa: SLF001
            decision = self.runtime.propose_decision(
                identity=identity,
                evidence=["EVD-CRK1-001"],
            )
            try:
                self.runtime.execute_decision(decision.id)
                results.append(
                    self._record("B2", "B2-06", "Shadow Outcome (no outcome on execute)", "FAILED")
                )
            except ConstitutionalError:
                results.append(
                    self._record("B2", "B2-06", "Shadow Outcome (no outcome on execute)", "REJECTED")
                )
        finally:
            self.runtime._disable_outcome_creation = shadow  # noqa: SLF001

        return results

    def run_class_b_structural(self, identity: str) -> list[RedTeamAttackResult]:
        return self.run_class_b2_structural(identity)

    def run_class_b3_semantic(self) -> list[RedTeamAttackResult]:
        results: list[RedTeamAttackResult] = []
        ce0, se0 = self._measure_exposure()

        frames = self.runtime.get_all_interpretations()
        dominant = max(frames, key=lambda frame: frame.weight)
        original_weight = dominant.weight
        try:
            dominant.weight = 1.0
            self.semantic_auditor.check_monoculture()
            results.append(
                self._record(
                    "B3",
                    "B3-01",
                    "Single frame weight 1.0",
                    "FAILED",
                    ce_before=ce0,
                    se_before=se0,
                )
            )
        except ConstitutionalError:
            results.append(
                self._record(
                    "B3",
                    "B3-01",
                    "Single frame weight 1.0",
                    "REJECTED",
                    ce_before=ce0,
                    se_before=se0,
                )
            )
        finally:
            dominant.weight = original_weight
            self.runtime._semantic._normalize_weights()  # noqa: SLF001

        adversarial = [frame for frame in frames if frame.adversarial]
        if adversarial:
            frame = adversarial[0]
            original = frame.adversarial
            try:
                frame.adversarial = False
                self.semantic_auditor.check_adversarial_loss()
                results.append(
                    self._record("B3", "B3-02", "Remove all adversarial frames", "FAILED")
                )
            except ConstitutionalError:
                results.append(
                    self._record("B3", "B3-02", "Remove all adversarial frames", "REJECTED")
                )
            finally:
                frame.adversarial = original
        else:
            results.append(
                self._record(
                    "B3",
                    "B3-02",
                    "Remove all adversarial frames",
                    "REJECTED",
                    "no adversarial frames to remove",
                )
            )

        bound = frames[0]
        original_binding = bound.prediction_binding
        try:
            bound.prediction_binding = False
            from src.crk1.semantic_reproduction_harness import SemanticReproductionHarness

            harness = SemanticReproductionHarness(
                self.runtime,
                SemanticExposureMonitor(self.runtime),
            )
            if harness.test_prediction_binding():
                results.append(
                    self._record("B3", "B3-03", "Interpretations with no predictions", "FAILED")
                )
            else:
                results.append(
                    self._record("B3", "B3-03", "Interpretations with no predictions", "REJECTED")
                )
        finally:
            bound.prediction_binding = original_binding

        original_weights = {frame.id: frame.weight for frame in frames}
        try:
            dominant = max(frames, key=lambda frame: frame.weight)
            for frame in frames:
                if frame.id != dominant.id:
                    frame.weight = 0.0
            try:
                exposure = SemanticExposureMonitor(self.runtime).measure_exposure()
                results.append(
                    self._record(
                        "B3",
                        "B3-04",
                        "SE(S) forced toward 0 via weight games",
                        "PASS" if exposure > 0 else "FAILED",
                        f"SE={exposure:.4f}",
                    )
                )
            except ConstitutionalError as exc:
                results.append(
                    self._record(
                        "B3",
                        "B3-04",
                        "SE(S) forced toward 0 via weight games",
                        "REJECTED",
                        str(exc),
                    )
                )
        finally:
            for frame in frames:
                frame.weight = original_weights[frame.id]
            self.runtime._semantic._normalize_weights()  # noqa: SLF001

        try:
            self.semantic_auditor.audit()
            ce1, se1 = self._measure_exposure()
            results.append(
                self._record(
                    "B3",
                    "B3-05",
                    "Semantic exposure audit",
                    "PASS",
                    ce_before=ce0,
                    se_before=se0,
                    ce_after=ce1,
                    se_after=se1,
                )
            )
        except ConstitutionalError as exc:
            results.append(
                self._record("B3", "B3-05", "Semantic exposure audit", "REJECTED", str(exc))
            )

        return results

    def run_class_c_semantic(self) -> list[RedTeamAttackResult]:
        return self.run_class_b3_semantic()

    def run_class_b4_founder(self) -> list[RedTeamAttackResult]:
        results: list[RedTeamAttackResult] = []
        prepare_continuity_substrate(self.runtime)

        ok, missing = verify_packet_artifacts()
        results.append(
            self._record(
                "B4",
                "B4-01",
                "Hidden config not in ledgers (packet completeness)",
                "PASS" if ok else "FAILED",
                "ok" if ok else f"missing: {', '.join(missing[:3])}",
            )
        )

        from src.crk1.runtime_validator import DEFAULT_INVARIANTS_PATH
        import yaml

        with DEFAULT_INVARIANTS_PATH.open(encoding="utf-8") as handle:
            doc = yaml.safe_load(handle)
        from src.crk1.external_reproduction_harness import ExternalReproductionHarness

        required = ExternalReproductionHarness.REQUIRED_INVARIANT_KEYS
        invs = doc.get("invariants") or {}
        yaml_ok = all(key in invs for key in required)
        results.append(
            self._record(
                "B4",
                "B4-02",
                "Invariants only in docs/comments (yaml registry)",
                "PASS" if yaml_ok else "FAILED",
                f"{len(invs)} laws in yaml",
            )
        )

        prepare_continuity_substrate(self.runtime)
        monitor = SemanticExposureMonitor(self.runtime)
        self.runtime.attach_semantic_monitor(monitor)
        monitor.snapshot()
        monitor.simulate_drift()
        harness_results = SemanticReproductionHarness(self.runtime, monitor).run()
        results.append(
            self._record(
                "B4",
                "B4-03",
                "Founder-only override (A7 semantic harness)",
                "PASS" if harness_results.get("founder_independent_reproduction") else "FAILED",
                str({k: v for k, v in harness_results.items() if not v}),
            )
        )

        try:
            from src.crk1.semantic_ledger import bootstrap_semantic_ledger

            ledger = bootstrap_semantic_ledger(self.runtime)
            gap = len(self.runtime.get_all_interpretations()) - sum(
                1 for entry in ledger.entries if entry.entry_type == "InterpretationObject"
            )
            results.append(
                self._record(
                    "B4",
                    "B4-04",
                    "Non-ledgered interpretive state",
                    "PASS" if gap == 0 else "FAILED",
                    f"interpretation gap={gap}",
                )
            )
        except Exception as exc:
            results.append(
                self._record("B4", "B4-04", "Non-ledgered interpretive state", "FAILED", str(exc))
            )

        hidden_decision = CRK1Decision(
            id="DEC-hidden",
            identity_id=self.runtime.kernel.ledgers.identity.id,
            evidence_refs=[],
        )
        try:
            self.runtime.save_decision(hidden_decision)
            results.append(self._record("B4", "B4-05", "Magic founder-only decision bypass", "FAILED"))
        except ConstitutionalError:
            results.append(
                self._record("B4", "B4-05", "Magic founder-only decision bypass", "REJECTED")
            )

        return results

    def run_class_d_founder(self) -> list[RedTeamAttackResult]:
        return self.run_class_b4_founder()

    def run_all(self, identity: str | None = None) -> RedTeamReport:
        identity_id = identity or self.runtime.kernel.ledgers.identity.id
        prepare_continuity_substrate(self.runtime)
        report = RedTeamReport()
        report.attacks = (
            self.run_class_b1_mechanical(identity_id)
            + self.run_class_b2_structural(identity_id)
            + self.run_class_b3_semantic()
            + self.run_class_b4_founder()
        )
        return report
