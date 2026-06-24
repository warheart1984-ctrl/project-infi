"""Machine-readable invariant spec — CI / dashboard smoke tests."""

from __future__ import annotations

from pathlib import Path

import yaml

from src.crk1.runtime_validator import CRK1RuntimeValidator, DEFAULT_INVARIANTS_PATH

REQUIRED_K0_K3 = (
    "K0_ConsequenceTransmission",
    "K1_ImmutableExposure",
    "K2_JudgmentConsequenceCoupling",
    "K3_AntiInsulation",
)

REQUIRED_K7_K12 = (
    "K7_InterpretivePluralism",
    "K8_PredictionBoundInterpretation",
    "K9_AntiMonoculture",
    "K10_AdversarialReconstruction",
    "K11_InterpretiveDriftEnvelope",
    "K12_SemanticExposureMetric",
)


def test_invariants_yaml_loads() -> None:
    with DEFAULT_INVARIANTS_PATH.open(encoding="utf-8") as handle:
        doc = yaml.safe_load(handle)
    assert doc["version"] == "1.0"
    assert doc["spec"] == "CRK-1 Constitutional Runtime Invariants"


def test_k0_k3_checks_present() -> None:
    validator = CRK1RuntimeValidator()
    invs = validator.invariants.get("invariants") or {}
    for key in REQUIRED_K0_K3:
        assert key in invs, f"missing invariant block: {key}"
        checks = invs[key].get("checks") or []
        assert checks, f"{key} must define checks"


def test_k7_k12_checks_present() -> None:
    validator = CRK1RuntimeValidator()
    invs = validator.invariants.get("invariants") or {}
    for key in REQUIRED_K7_K12:
        assert key in invs, f"missing semantic invariant block: {key}"
        checks = invs[key].get("checks") or []
        assert checks, f"{key} must define checks"


def test_k1_forbidden_operations_include_delete_outcome() -> None:
    validator = CRK1RuntimeValidator()
    forbidden = validator.list_forbidden_operations()
    assert "delete(Outcome)" in forbidden
    assert "mark_evidence_irrelevant_for_identity(evidence, identity)" in forbidden


def test_badge_assets_exist() -> None:
    badge_dir = Path(DEFAULT_INVARIANTS_PATH).parent / "crk1_continuity_badges"
    for name in (
        "continuity_pass.svg",
        "continuity_fail.svg",
        "insulation_detected.svg",
        "lineage_break_detected.svg",
        "evidence_suppression_detected.svg",
    ):
        assert (badge_dir / name).is_file(), f"missing badge: {name}"
