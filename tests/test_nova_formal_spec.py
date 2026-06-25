"""Tests for Nova Cortex formal model helpers."""

from __future__ import annotations

from src.cog_runtime.formal.activation_predicates import (
    evaluate_activation,
    explicit_deliberation,
    frame_kind,
    phi_delib,
)
from src.cog_runtime.formal.agency_preservation import check_agency_preservation
from src.cog_runtime.formal.distributed_ledger import merge_ledger_entries
from src.cog_runtime.formal.generation_gate import (
    generation_verification_enabled,
    run_generation_with_verification,
)
from src.cog_runtime.formal.intent_narrative_reconcile import reconcile_intent_narrative
from src.cog_runtime.formal.ledger_schema import compress_ledger_entry, validate_ledger_entry
from src.cog_runtime.formal.output_constraints import resample_until_valid, verify_output_constraints
from src.cog_runtime.formal.output_type_governance import validate_cortex_output_typing
from src.cog_runtime.formal.spine_pipeline import evaluate_spine_pipeline
from src.cog_runtime import nova_cortex_spec
from src.cog_runtime.tuning import detect_tuning_env_change, reset_tuned_thresholds, run_self_tune_invariants
from src.speaking_runtime import verify_reply


def test_phi_delib_decidable():
    sigma = {"user_message": "should I pick A or B?", "response_mode": ""}
    assert frame_kind(sigma) == "decision"
    assert phi_delib(sigma) is True
    assert explicit_deliberation(sigma) is False

    sigma2 = {"user_message": "explain widgets", "response_mode": "think", "frame_kind": "decision"}
    assert explicit_deliberation(sigma2) is True
    assert evaluate_activation("cognitive.deliberation", sigma2)["active"] is True


def test_ledger_schema_validation():
    entry = {
        "runtime_id": "cognitive.attention",
        "stage": "focus",
        "trace_id": "abc",
        "started_at": "2026-05-29T12:00:00Z",
        "ended_at": "2026-05-29T12:00:01Z",
        "payload": {"frame_kind": "general"},
        "result": {"artifact_key": "focus_artifact"},
    }
    assert validate_ledger_entry(entry)["valid"] is True
    compressed = compress_ledger_entry(
        {
            **entry,
            "payload": {"user_message": "x" * 600},
        }
    )
    assert len(compressed["payload"]["user_message"]) <= 512


def test_theorem_5_1_typing_gate():
    result = validate_cortex_output_typing(nova_cortex_spec())
    assert result["valid"] is True
    bad = validate_cortex_output_typing(
        {
            "runtimes": [
                {
                    "id": "bad.lobe",
                    "outputs": {"tool_call": "object"},
                }
            ]
        }
    )
    assert bad["valid"] is False


def test_verify_output_constraints_with_focus():
    text = (
        "**Listen** — understood.\n**Frame** — design.\n**Plan** — answer.\n"
        "**Speak** — focused on deployment safety.\n"
        "**Check** — here's what i think i did; say so if you want more."
    )
    focus = {"primary_focus": "deployment safety", "secondary_focus": ""}
    result = verify_output_constraints(text, focus_artifact=focus, speaking_validation={"valid": True, "issues": []})
    assert result["valid"] is True

    bad = verify_output_constraints(
        "I'll ship this now.",
        focus_artifact={"primary_focus": "deployment safety"},
    )
    assert bad["valid"] is False


def test_verify_reply_combines_speaking_and_constraints():
    good = (
        "**Listen** — ok.\n**Frame** — question.\n**Plan** — answer.\n"
        "**Speak** — deployment safety first.\n"
        "**Check** — here's what i think i did; say so."
    )
    assert verify_reply(good, focus_artifact={"primary_focus": "deployment safety"})["valid"] is True


def test_resample_until_valid():
    attempts = {"n": 0}

    def speak_fn():
        attempts["n"] += 1
        if attempts["n"] < 2:
            return "too short"
        return (
            "**Listen** — ok.\n**Frame** — question.\n**Plan** — answer.\n"
            "**Speak** — deployment safety.\n"
            "**Check** — here's what i think i did; say so."
        )

    body, meta = resample_until_valid(
        speak_fn,
        max_attempts=3,
        focus_artifact={"primary_focus": "deployment safety"},
    )
    assert meta["final_valid"] is True
    assert meta["resampled"] is True
    assert "deployment safety" in body


def test_intent_narrative_reconcile():
    intent = {
        "active_commitments": [
            {"id": "c1", "status": "resolved", "text": "done"},
            {"id": "c2", "status": "active", "text": "keep going"},
        ],
        "protected_values": ["identity_consistency"],
        "current_tensions": [],
    }
    narrative = {
        "active_story": "new arc",
        "promises": [{"commitment_id": "c3", "status": "open", "text": "orphan"}],
    }
    prior = {"active_story": "old arc"}
    result = reconcile_intent_narrative(intent, narrative, prior_intent=prior)
    assert result["valid"] is False
    assert any("dangling_promise" in issue for issue in result["issues"])
    assert result["reconciliation"]["story_changed"] is True


def test_spine_pipeline_halt_on_false():
    halted = evaluate_spine_pipeline({"require_substrate": True, "substrate_ok": False})
    assert halted["halted"] is True
    assert halted["halt_stage"] == "rls_substrate"

    ok = evaluate_spine_pipeline({"substrate_ok": True, "cognitive_runtime_enabled": True})
    assert ok["halted"] is False
    assert len(ok["trace"]) == 4


def test_agency_preservation_detects_dropped_commitment():
    prior = {"active_commitments": [{"id": "c1", "status": "active", "commitment": "ship safely"}]}
    current = {
        "active_commitments": [],
        "protected_values": [
            "jarvis_executive_authority",
            "operator_safety",
            "proof_over_assertion",
            "identity_consistency",
        ],
    }
    result = check_agency_preservation(prior, current, {"core_identity": "Nova is a governed companion inside AAIS; Jarvis retains executive authority."})
    assert result["valid"] is False
    assert any("usurpation:dropped_commitment" in issue for issue in result["issues"])


def test_generation_gate_resample():
    class Session:
        metadata = {
            "speaking_runtime_enabled": True,
            "cognitive_runtime_enabled": False,
        }

    session = Session()
    calls = {"n": 0}

    def generate_fn():
        calls["n"] += 1
        if calls["n"] == 1:
            return "too short"
        return (
            "**Listen** — ok.\n**Frame** — question.\n**Plan** — answer.\n"
            "**Speak** — deployment safety.\n"
            "**Check** — here's what i think i did; say so."
        )

    text = run_generation_with_verification(session, generate_fn, user_message="focus on deployment safety")
    assert calls["n"] == 2
    assert "deployment safety" in text
    assert session.metadata["output_verification_trace"]["final_valid"] is True


def test_distributed_ledger_merge():
    local = [{"trace_id": "a1", "runtime_id": "cognitive.attention", "started_at": "2026-05-29T12:00:00Z", "vector_clock": {"node_a": 1}}]
    remote = [{"trace_id": "b1", "runtime_id": "cognitive.memory", "started_at": "2026-05-29T12:00:01Z", "vector_clock": {"node_b": 1}}]
    merged, report = merge_ledger_entries(local, remote, node_id="node_a")
    assert len(merged) == 2
    assert report["merged_count"] == 2


def test_tuning_env_reset():
    prior = {
        "tuning_history": [
            {"trigger_verification": "failed", "trigger_alignment": "misaligned"},
            {"trigger_verification": "failed", "trigger_alignment": "misaligned"},
            {"trigger_verification": "failed", "trigger_alignment": "misaligned"},
            {"trigger_verification": "failed", "trigger_alignment": "misaligned"},
            {"trigger_verification": "failed", "trigger_alignment": "misaligned"},
        ]
    }
    assert detect_tuning_env_change(prior) is True
    reset = reset_tuned_thresholds(reason="test")
    assert reset["env_reset"] is True
    tuned = run_self_tune_invariants({}, prior_tuning=prior)
    assert tuned.get("env_reset") is True
