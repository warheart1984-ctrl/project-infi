"""CRK-1 External Reproduction Harness — Mission #003 Part I."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

import yaml

from src.crk1.consequence_lattice import consequence_exposure
from src.crk1.founder_independent_semantic_audit import FounderIndependentSemanticAudit
from src.crk1.kernel_ledger import bootstrap_kernel_ledger_entry
from src.crk1.mutation_ledger import CRK1MutationLedger
from src.crk1.runtime_validator import CRK1RuntimeValidator, DEFAULT_INVARIANTS_PATH
from src.crk1.schema_validator import CRK1SchemaValidator
from src.crk1.mission_003_packet import verify_packet_artifacts
from src.crk1.semantic_reproduction_harness import SemanticReproductionHarness
from src.crk1.semantic_exposure_monitor import SemanticExposureMonitor
from src.crk1.semantic_ledger import bootstrap_semantic_ledger

if TYPE_CHECKING:
    from src.crk1.runtime_facade import CRK1Runtime

REPO_ROOT = Path(__file__).resolve().parents[2]
CODEX_PATH = REPO_ROOT / "docs" / "crk1" / "crk1_kernel_codex.md"
SCHEMA_DIR = REPO_ROOT / "fixtures" / "crk1"

SCHEMA_FILES = {
    "OutcomeObject": "outcome_object.schema.json",
    "EvidenceObject": "evidence_object.schema.json",
    "DecisionObject": "decision_object.schema.json",
    "IdentityObject": "identity_object.schema.json",
    "InterpretationObject": "interpretation_object.schema.json",
}


def prepare_continuity_substrate(runtime: CRK1Runtime) -> None:
    """Warm interpretive substrate using only public runtime APIs."""
    root = runtime.kernel.ledgers.identity.id
    runtime.propose_and_execute(identity=root, evidence=["EVD-CRK1-001"])
    evidence = runtime.create_evidence()
    frame = runtime.get_dominant_interpretation()
    prediction = runtime.generate_prediction(frame.id, evidence.id)
    outcome = runtime.realize_outcome_from_prediction(prediction.id)
    replayed = runtime.replay_outcome(outcome.id)
    runtime.update_interpretation(frame.id, replayed.id)
    runtime.get_reconstructions_for_evidence(evidence.id)


@dataclass
class ReproductionStepResult:
    step_id: str
    name: str
    passed: bool
    detail: str = ""


@dataclass
class ExternalReproductionReport:
    steps: list[ReproductionStepResult] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return all(step.passed for step in self.steps)

    def summary(self) -> str:
        lines = ["CRK-1 External Reproduction Harness"]
        for step in self.steps:
            status = "PASS" if step.passed else "FAIL"
            lines.append(f"  [{status}] {step.step_id}: {step.name}")
            if step.detail:
                lines.append(f"         {step.detail}")
        lines.append(f"Overall: {'PASS' if self.passed else 'FAIL'}")
        return "\n".join(lines)


class ExternalReproductionHarness:
    """Rebuild and verify CRK-1 from continuity substrate without founder knowledge."""

    REQUIRED_INVARIANT_KEYS = (
        "K0_ConsequenceTransmission",
        "K1_ImmutableExposure",
        "K2_JudgmentConsequenceCoupling",
        "K3_AntiInsulation",
        "K4_ConsequencePreservationLaw",
        "K5_MutationAdmissibilityTest",
        "K6_ConstitutionalDriftEnvelope",
        "K7_InterpretivePluralism",
        "K8_PredictionBoundInterpretation",
        "K9_AntiMonoculture",
        "K10_AdversarialReconstruction",
        "K11_InterpretiveDriftEnvelope",
        "K12_SemanticExposureMetric",
    )

    REQUIRED_SCHEMAS = (
        "OutcomeObject",
        "EvidenceObject",
        "DecisionObject",
        "IdentityObject",
        "InterpretationObject",
    )

    def __init__(self, runtime: CRK1Runtime) -> None:
        self.runtime = runtime
        self.validator = CRK1RuntimeValidator()
        self.schema_validator = CRK1SchemaValidator()

    def step_artifacts_present(self) -> ReproductionStepResult:
        passed, missing = verify_packet_artifacts()
        return ReproductionStepResult(
            "REP-0",
            "M3-A packet artifacts (A1–A7)",
            passed,
            "ok" if passed else f"missing: {', '.join(missing[:5])}",
        )

    def step_five_objects(self) -> ReproductionStepResult:
        try:
            identity = self.runtime.kernel.ledgers.identity
            evidence = self.runtime.create_evidence()
            decision = self.runtime.propose_decision(
                identity=identity.id,
                evidence=[evidence.id],
            )
            outcome = self.runtime.execute_decision(decision.id)
            frames = self.runtime.get_all_interpretations()
            passed = all(
                [
                    identity is not None,
                    decision is not None,
                    outcome is not None,
                    evidence is not None,
                    len(frames) >= 2,
                ]
            )
            return ReproductionStepResult(
                "REP-1",
                "Five objects rebuilt",
                passed,
                f"Identity, Decision, Outcome, Evidence, {len(frames)} Interpretation(s)",
            )
        except Exception as exc:
            return ReproductionStepResult("REP-1", "Five objects rebuilt", False, str(exc))

    def step_consequence_loop(self) -> ReproductionStepResult:
        try:
            entry = bootstrap_kernel_ledger_entry(self.runtime)
            anchors = entry.replay_anchors
            passed = bool(anchors.decision_d0.evidence) and anchors.evidence_e1.replay_of == anchors.outcome_o0.id
            return ReproductionStepResult(
                "REP-2",
                "Consequence loop anchored",
                passed,
                f"D0→O0→E1 replay_of={anchors.evidence_e1.replay_of}",
            )
        except Exception as exc:
            return ReproductionStepResult("REP-2", "Consequence loop anchored", False, str(exc))

    def step_semantic_loop(self) -> ReproductionStepResult:
        try:
            ledger = bootstrap_semantic_ledger(self.runtime)
            passed = len(ledger.entries) >= 2 and bool(ledger.signature)
            return ReproductionStepResult(
                "REP-3",
                "Semantic loop ledgered",
                passed,
                f"{len(ledger.entries)} semantic entries; sig={ledger.signature[:16]}...",
            )
        except Exception as exc:
            return ReproductionStepResult("REP-3", "Semantic loop ledgered", False, str(exc))

    def step_exposure_metrics(self) -> ReproductionStepResult:
        try:
            ce = consequence_exposure(self.runtime).score
            se = SemanticExposureMonitor(self.runtime).measure_exposure()
            passed = ce > 0 and se > 0
            return ReproductionStepResult(
                "REP-4",
                "CE(S) and SE(S) measurable",
                passed,
                f"CE={ce:.4f} SE={se:.4f}",
            )
        except Exception as exc:
            return ReproductionStepResult("REP-4", "CE(S) and SE(S) measurable", False, str(exc))

    def step_invariants_k0_k12(self) -> ReproductionStepResult:
        try:
            with DEFAULT_INVARIANTS_PATH.open(encoding="utf-8") as handle:
                doc = yaml.safe_load(handle)
            invs = doc.get("invariants") or {}
            missing = [key for key in self.REQUIRED_INVARIANT_KEYS if key not in invs]
            forbidden = self.validator.list_forbidden_operations()
            passed = not missing and len(forbidden) >= 2
            return ReproductionStepResult(
                "REP-5",
                "Invariants K0–K12 in yaml",
                passed,
                f"{len(self.REQUIRED_INVARIANT_KEYS) - len(missing)} laws; "
                f"{len(forbidden)} forbidden ops",
            )
        except Exception as exc:
            return ReproductionStepResult("REP-5", "Invariants K0–K12 in yaml", False, str(exc))

    def step_governance_cycle(self) -> ReproductionStepResult:
        try:
            from src.crk1.governance_engine import GovernanceEngine

            engine = GovernanceEngine(self.runtime, self.validator)
            identity = self.runtime.kernel.ledgers.identity.id
            decision = engine.propose(
                identity,
                {
                    "type": "parameter_change",
                    "content": {"governance.quorum": 3},
                    "justification": "reproduction test",
                    "evidence_ids": ["EVD-CRK1-001"],
                },
            )
            engine.deliberate(decision.id, [{"reviewer": "neutral", "verdict": "approve"}])
            outcome, evidence = engine.ratify(decision.id)
            passed = outcome is not None and evidence is not None
            return ReproductionStepResult(
                "REP-6",
                "Governance cycle",
                passed,
                f"propose→deliberate→ratify; outcome={outcome.id}",
            )
        except Exception as exc:
            return ReproductionStepResult("REP-6", "Governance cycle", False, str(exc))

    def step_semantic_reproduction_harness(self) -> ReproductionStepResult:
        try:
            prepare_continuity_substrate(self.runtime)
            monitor = SemanticExposureMonitor(self.runtime)
            self.runtime.attach_semantic_monitor(monitor)
            monitor.snapshot()
            monitor.simulate_drift()
            results = SemanticReproductionHarness(self.runtime, monitor).run()
            passed = bool(results.get("founder_independent_reproduction"))
            failed = [key for key, ok in results.items() if key != "founder_independent_reproduction" and not ok]
            return ReproductionStepResult(
                "REP-7",
                "A7 SemanticReproductionHarness (K7–K12)",
                passed,
                "all K7–K12 pass" if passed else f"failed: {', '.join(failed)}",
            )
        except Exception as exc:
            return ReproductionStepResult(
                "REP-7",
                "A7 SemanticReproductionHarness (K7–K12)",
                False,
                str(exc),
            )

    def step_founder_independent_semantic(self) -> ReproductionStepResult:
        prepare_continuity_substrate(self.runtime)
        report = FounderIndependentSemanticAudit(self.runtime).run_all()
        return ReproductionStepResult(
            "REP-8",
            "Founder-independent semantic audit (FIT)",
            report.passed,
            report.summary().split("\n")[-1],
        )

    def step_mutation_ledger_ready(self) -> ReproductionStepResult:
        ledger = CRK1MutationLedger()
        passed = ledger.version == "1.0"
        return ReproductionStepResult(
            "REP-9",
            "Mutation ledger substrate",
            passed,
            f"ledger_type={ledger.ledger_type}",
        )

    def run_all(self) -> ExternalReproductionReport:
        report = ExternalReproductionReport()
        artifact_step = self.step_artifacts_present()
        if artifact_step.passed:
            prepare_continuity_substrate(self.runtime)
        report.steps = [
            artifact_step,
            self.step_five_objects(),
            self.step_consequence_loop(),
            self.step_semantic_loop(),
            self.step_exposure_metrics(),
            self.step_invariants_k0_k12(),
            self.step_governance_cycle(),
            self.step_semantic_reproduction_harness(),
            self.step_founder_independent_semantic(),
            self.step_mutation_ledger_ready(),
        ]
        return report
