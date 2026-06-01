"""Tests for AI Factory Wolf payload deploy (v1.1)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from ai_factory.orchestrator import deploy_active_build, run_build
from ai_factory.wolf_deploy import deploy_build_to_wolf_payload

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SPEC = REPO_ROOT / "factory/specs/nova-default.yaml"


def test_wolf_deploy_copies_payload_artifacts(tmp_path: Path) -> None:
    if not DEFAULT_SPEC.is_file():
        pytest.skip("reference spec missing")

    runtime_root = tmp_path / "factory_out"
    result = run_build(
        spec_path=DEFAULT_SPEC,
        repo_root=REPO_ROOT,
        runtime_root=runtime_root,
        skip_pytest=True,
        fixed_timestamp="2026-05-31T12:00:00+00:00",
        ledger_path=tmp_path / "ledger.jsonl",
    )
    wolf_root = tmp_path / "wolf_payload"
    receipt = deploy_build_to_wolf_payload(
        build_id=result.build_id,
        runtime_root=runtime_root,
        repo_root=REPO_ROOT,
        wolf_payload_root=wolf_root,
    )
    assert receipt["build_id"] == "nova-default"
    family_path = wolf_root / "cognitive_runtime_family.json"
    assert family_path.is_file()
    family = json.loads(family_path.read_text(encoding="utf-8"))
    assert family.get("family_id") == "nova.cortex"


def test_deploy_active_build_with_wolf_flag(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    if not DEFAULT_SPEC.is_file():
        pytest.skip("reference spec missing")

    runtime_root = tmp_path / "factory_out"
    monkeypatch.chdir(REPO_ROOT)
    run_build(
        spec_path=DEFAULT_SPEC,
        repo_root=REPO_ROOT,
        runtime_root=runtime_root,
        skip_pytest=True,
        fixed_timestamp="2026-05-31T12:00:00+00:00",
        ledger_path=tmp_path / "ledger.jsonl",
    )
    wolf_root = tmp_path / "wolf_payload"
    pointer = deploy_active_build(
        build_id="nova-default",
        runtime_root=runtime_root,
        repo_root=REPO_ROOT,
        wolf_payload_root=wolf_root,
        wolf_deploy=True,
    )
    assert pointer.is_file()
    assert (wolf_root / "cognitive_runtime_family.json").is_file()
