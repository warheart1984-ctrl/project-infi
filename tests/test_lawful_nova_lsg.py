"""Lawful Nova LSG bootstrap, conversation grounding, and UGR invariant tests."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from nova.exceptions import GovernanceViolationError
from nova.governance import seams
from nova.lawful_llm import LawfulLLM
from nova.lsg_loader import compile_bundle_facts, default_lsg_bundle_path, load_lsg_bundle
from nova.runtime_factory import build_lawful_llm


@pytest.fixture(autouse=True)
def _reset_seams():
    from nova.governance.cvr_recompute import reset_cvr_registry_for_tests

    seams.reset_seams_for_tests()
    reset_cvr_registry_for_tests()
    yield
    seams.reset_seams_for_tests()
    reset_cvr_registry_for_tests()


@pytest.fixture
def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


@pytest.fixture
def seeded_store(tmp_path, repo_root, monkeypatch):
    store_path = tmp_path / "lsg" / "local.jsonl"
    bundle_path = repo_root / "lsg" / "LSG-CORE.v1.yaml"
    monkeypatch.setenv("NOVA_LSG_STORE", str(store_path))
    monkeypatch.setenv("NOVA_LSG_PATH", str(bundle_path))
    monkeypatch.setenv("LAWFUL_NOVA_REPO_ROOT", str(repo_root))
    load_lsg_bundle(bundle_path, tenant_id="local", store_path=store_path)
    return store_path


def test_lsg_bootstrap_loads(repo_root):
    bundle_path = repo_root / "lsg" / "LSG-CORE.v1.yaml"
    assert bundle_path.exists()
    raw = bundle_path.read_text(encoding="utf-8")
    assert "bundle_id: LSG-CORE" in raw
    triples = compile_bundle_facts(__import__("yaml").safe_load(raw))
    assert len(triples) >= 10


def test_conversation_hello(seeded_store):
    llm = build_lawful_llm(operator_session_id="test-session", signing_secret="test-secret")
    turn = llm.ask("hello", tenant_id="local", capability="observe")
    assert "no matching LSG facts" not in turn.text.lower()
    assert turn.voss_runtime["decision"] == "EXECUTED"
    assert llm.verify_receipt(turn.receipt) is True


def test_conversation_how_are_you(seeded_store):
    llm = build_lawful_llm(operator_session_id="test-session", signing_secret="test-secret")
    turn = llm.ask("how are you", tenant_id="local", capability="observe")
    assert "no matching LSG facts" not in turn.text.lower()
    assert turn.nova_cortex["lsg"]["facts_used"]


def test_fallback_on_nonsense(seeded_store):
    llm = build_lawful_llm(operator_session_id="test-session", signing_secret="test-secret")
    turn = llm.ask("xyzzyplugh999", tenant_id="local", capability="observe")
    assert "no matching lsg facts" in turn.text.lower()
    assert turn.voss_runtime["decision"] == "EXECUTED"


def test_reproducibility(seeded_store):
    llm = build_lawful_llm(operator_session_id="test-session", signing_secret="test-secret")
    first = llm.ask("hello", tenant_id="local", capability="observe")
    second = llm.ask("hello", tenant_id="local", capability="observe")
    assert first.text == second.text
    receipt_one = json.loads(first.receipt["payload"])
    receipt_two = json.loads(second.receipt["payload"])
    assert receipt_one["memory_facts_used"] == receipt_two["memory_facts_used"]


def test_ugr_invariants_pass(seeded_store):
    llm = build_lawful_llm(operator_session_id="test-session", signing_secret="test-secret")
    turn = llm.ask("hello", tenant_id="local", capability="observe")
    payload = json.loads(turn.receipt["payload"])
    invariants = payload.get("continuity_invariants") or {}
    assert len(invariants) == 7
    assert all(entry.get("status") == "pass" for entry in invariants.values())


def test_ugr_strict_fails_without_lsg(monkeypatch):
    monkeypatch.setenv("NOVA_UGR_STRICT", "1")
    llm = LawfulLLM(operator_session_id="test-session", signing_secret="test-secret")
    with pytest.raises(GovernanceViolationError, match="UGR continuity invariant failure"):
        llm.ask("explain gravity", tenant_id="local", capability="reason")


def test_lawful_turn_recomputes_cvr(seeded_store):
    llm = build_lawful_llm(operator_session_id="test-session", signing_secret="test-secret")
    turn = llm.ask("hello", tenant_id="local", capability="observe")
    payload = json.loads(turn.receipt["payload"])
    governance = payload.get("continuity_governance") or {}
    assert governance.get("cvr")
    assert governance["cvr"]["derived_score"] > 0
    assert governance.get("proof", {}).get("status") == "PROVEN"
    assert governance.get("continuity_trace", {}).get("trace_hash")
    assert turn.continuity_governance == governance


def test_cvr_accumulates_across_turns(seeded_store):
    llm = build_lawful_llm(operator_session_id="test-session", signing_secret="test-secret")
    first = llm.ask("hello", tenant_id="local", capability="observe")
    second = llm.ask("how are you", tenant_id="local", capability="observe")
    first_cvr = json.loads(first.receipt["payload"])["continuity_governance"]["cvr"]
    second_cvr = json.loads(second.receipt["payload"])["continuity_governance"]["cvr"]
    assert second_cvr["metrics"]["proofs_count"] == first_cvr["metrics"]["proofs_count"] + 1
    assert len(second_cvr["basis"]["proofs"]) == 2
