"""Tests for AI Factory v1 governed mind fabrication."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from ai_factory.binding import build_bound_capability_profile
from ai_factory.envelope import build_receipt
from ai_factory.orchestrator import FactoryBuildError, run_build
from ai_factory.spec import AIBuildSpec, load_build_spec, run_spec_station
from ai_factory.spine_profile import build_spine_profile, build_turn_context_from_profile
from ai_factory.runtime_bundle import build_cortex_runtime_bundle


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SPEC = REPO_ROOT / "factory/specs/nova-default.yaml"


@pytest.fixture()
def nova_spec() -> AIBuildSpec:
    if not DEFAULT_SPEC.is_file():
        pytest.skip("reference spec missing")
    return load_build_spec(DEFAULT_SPEC)


def test_load_nova_default_spec(nova_spec: AIBuildSpec) -> None:
    assert nova_spec.build_id == "nova-default"
    assert nova_spec.spec_version == "ai_factory.ai_build_spec.v1"
    assert "speaking.runtime" in nova_spec.capabilities.enabled_lobes
    assert nova_spec.risk_level == "low"


def test_spec_station_writes_canonical_json(tmp_path: Path) -> None:
    spec, receipt = run_spec_station(spec_path=DEFAULT_SPEC, output_dir=tmp_path)
    target = tmp_path / "AI_BUILD_SPEC.json"
    assert target.is_file()
    payload = json.loads(target.read_text(encoding="utf-8"))
    assert payload["build_id"] == spec.build_id
    assert receipt["status"] == "ok"


def test_spine_profile_high_risk_fail_closed() -> None:
    spec = AIBuildSpec(
        build_id="high-risk",
        intent_summary="test",
        risk_level="high",
    )
    profile = build_spine_profile(spec)
    assert profile["stages"]["rls_substrate"]["substrate_ok_default"] is False
    assert profile["stages"]["rls_substrate"]["fail_closed"] is True


def test_turn_context_from_profile_high_risk() -> None:
    spec = AIBuildSpec(build_id="high-risk", intent_summary="test", risk_level="high")
    profile = build_spine_profile(spec)
    ctx = build_turn_context_from_profile(profile)
    assert ctx["substrate_ok"] is False
    assert ctx["spine_profile_id"] == "high-risk.spine"


def test_cortex_runtime_bundle_shape(nova_spec: AIBuildSpec) -> None:
    profile = build_spine_profile(nova_spec)
    bundle = build_cortex_runtime_bundle(
        spec=nova_spec,
        spine_profile=profile,
        repo_root=REPO_ROOT,
    )
    assert bundle["bundle_id"] == "nova-default.cortex"
    assert bundle["family_spec"]["family_id"] == "nova.cortex"
    assert "jarvis.reasoning" in bundle["enabled_runtimes"]
    assert bundle["composed_spec"]["runtime_id"] == "aais.composed_turn"


def test_bound_capability_profile_stub(nova_spec: AIBuildSpec) -> None:
    profile = build_bound_capability_profile(nova_spec)
    assert profile["model_policy"] == "inherit_jarvis_default"
    assert profile["constraints"]["high_impact_actions_blocked"] is True


def test_build_receipt_hash_manifest(tmp_path: Path, nova_spec: AIBuildSpec) -> None:
    run_spec_station(spec_path=DEFAULT_SPEC, output_dir=tmp_path)
    from ai_factory.spine_profile import run_spine_station
    from ai_factory.runtime_bundle import run_runtime_station
    from ai_factory.binding import run_binding_station

    spine_profile, _ = run_spine_station(spec=nova_spec, output_dir=tmp_path)
    run_runtime_station(
        spec=nova_spec,
        spine_profile=spine_profile,
        output_dir=tmp_path,
        repo_root=REPO_ROOT,
    )
    run_binding_station(spec=nova_spec, output_dir=tmp_path)
    (tmp_path / "AI_PROOF_BUNDLE.md").write_text("# proof\n", encoding="utf-8")
    proof_manifest = {
        "claim_label": "asserted",
        "deploy_blocked": False,
        "verification_summary": {"lanes_run": 1, "lanes_passed": 1},
    }
    (tmp_path / "proof_manifest.json").write_text(json.dumps(proof_manifest), encoding="utf-8")
    receipt = build_receipt(
        spec=nova_spec,
        spine_profile=spine_profile,
        proof_manifest=proof_manifest,
        output_dir=tmp_path,
        station_receipts={"spec": {"status": "ok"}},
    )
    assert receipt["receipt_version"] == "ai_factory.build_receipt.v1"
    assert len(receipt["hash_manifest"]) >= 5
    assert all(item["exists"] for item in receipt["hash_manifest"])


def test_full_build_skip_pytest(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    runtime_root = tmp_path / "factory_out"
    monkeypatch.chdir(REPO_ROOT)
    result = run_build(
        spec_path=DEFAULT_SPEC,
        repo_root=REPO_ROOT,
        runtime_root=runtime_root,
        skip_pytest=True,
        fixed_timestamp="2026-05-31T00:00:00+00:00",
        ledger_path=tmp_path / "ledger.jsonl",
    )
    assert result.build_id == "nova-default"
    receipt_path = result.output_dir / "AI_BUILD_RECEIPT.json"
    assert receipt_path.is_file()
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    assert receipt["claim_label"] in {"asserted", "proven"}
    assert (result.output_dir / "CORTEX_RUNTIME_BUNDLE.json").is_file()


def test_build_rejects_invalid_spec(tmp_path: Path) -> None:
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps({"build_id": "x"}), encoding="utf-8")
    with pytest.raises(FactoryBuildError):
        run_build(
            spec_path=bad,
            repo_root=REPO_ROOT,
            runtime_root=tmp_path / "out",
            skip_pytest=True,
        )
