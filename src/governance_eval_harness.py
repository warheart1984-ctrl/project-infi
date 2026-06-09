"""Governance eval harness — training label parity and optional runtime replay."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from src.governance_taxonomy import TRAINING_LABELS
from src.invariant_compiler import compile_from_ir
from src.training_view_spec import TrainingViewRecord, infer_label_from_mask


def replay_label(record: TrainingViewRecord) -> str:
    """Recompute label via infer_label_from_mask on governance_ir_snapshot."""
    snapshot = dict(record.governance_ir_snapshot or {})
    return infer_label_from_mask(
        snapshot,
        action_type=record.action_type,
        verb=_verb_from_record(record),
        resource_class=record.resource_class,
    )


def _verb_from_record(record: TrainingViewRecord) -> str | None:
    delta = dict(record.authority_delta or {})
    verbs_added = list(delta.get("verbs_added") or ())
    if verbs_added:
        return str(verbs_added[0])
    return "observe"


def assert_label_parity(record: TrainingViewRecord) -> dict[str, Any]:
    """Returns {status, expected, actual, view_id}."""
    actual = replay_label(record)
    expected = str(record.label or "").strip().upper()
    if expected not in TRAINING_LABELS:
        return {
            "status": "fail",
            "expected": expected,
            "actual": actual,
            "view_id": record.view_id,
            "reason": "invalid_record_label",
        }
    if actual == expected:
        return {
            "status": "pass",
            "expected": expected,
            "actual": actual,
            "view_id": record.view_id,
        }
    if expected == "VIOLATION" and actual in {"VIOLATION", "BORDERLINE", "ESCALATE"}:
        return {
            "status": "pass",
            "expected": expected,
            "actual": actual,
            "view_id": record.view_id,
            "reason": "violation_family_match",
        }
    return {
        "status": "fail",
        "expected": expected,
        "actual": actual,
        "view_id": record.view_id,
    }


def _runtime_label_from_result(result: dict[str, Any]) -> str:
    status = str(result.get("status") or "").strip().upper()
    if status == "EXECUTED":
        return "COMPLIANT"
    if status in {"BLOCKED", "ESCALATED"}:
        return "VIOLATION"
    return "BORDERLINE"


def run_eval_suite(
    examples: list[TrainingViewRecord],
    *,
    include_runtime: bool = False,
    provider_id: str = "reference_mock",
) -> dict[str, Any]:
    """Run label parity checks; optionally replay through decode governance."""
    label_results: list[dict[str, Any]] = []
    runtime_results: list[dict[str, Any]] = []
    pass_count = 0
    fail_count = 0

    for record in examples:
        parity = assert_label_parity(record)
        label_results.append(parity)
        if parity.get("status") == "pass":
            pass_count += 1
        else:
            fail_count += 1

        if include_runtime:
            runtime_results.append(
                _runtime_replay_record(record, provider_id=provider_id, parity=parity)
            )

    runtime_pass = sum(1 for item in runtime_results if item.get("status") == "pass")
    runtime_fail = len(runtime_results) - runtime_pass

    return {
        "status": "pass" if fail_count == 0 else "fail",
        "label_parity": {
            "pass": pass_count,
            "fail": fail_count,
            "results": label_results,
        },
        "runtime_replay": {
            "enabled": include_runtime,
            "provider_id": provider_id,
            "pass": runtime_pass,
            "fail": runtime_fail,
            "results": runtime_results,
        },
        "example_count": len(examples),
    }


def _runtime_replay_record(
    record: TrainingViewRecord,
    *,
    provider_id: str,
    parity: dict[str, Any],
) -> dict[str, Any]:
    from unittest.mock import patch

    from src.aais_governed_llm_module import propose_governed_llm_envelope
    from src.decode_governance_executor import execute_with_decode_governance
    from tests.test_bridge_fixtures import build_test_bridge

    snapshot = dict(record.governance_ir_snapshot or {})
    if not snapshot.get("ir_fingerprint"):
        from tests.test_bridge_fixtures import build_test_ir

        snapshot = dict(build_test_ir(trace_id=f"eval-{record.view_id}"))

    bundle = compile_from_ir(snapshot)
    bridge = build_test_bridge(trace_id=f"eval-{record.view_id}")
    bridge["decode_governance_bundle"] = bundle
    envelope = propose_governed_llm_envelope(bridge)
    provider_request = dict(envelope.get("provider_request") or {})
    provider_request["provider"] = provider_id
    provider_request.setdefault("generation_overrides", {})
    provider_request["generation_overrides"].update({"temperature": 0.0, "max_tokens": 64})
    envelope = dict(envelope)
    envelope["provider_request"] = provider_request

    def fake_generator(*_args, **_kwargs):
        content = "ok" if record.label == "COMPLIANT" else "bad"
        return {
            "status": "EXECUTED",
            "content": content,
            "module_id": "eval",
            "provider": provider_id,
        }

    def passing_checkpoints(*_args, **_kwargs):
        return [
            {"name": "bridge_invariant", "status": "pass"},
            {"name": "governed_llm_envelope", "status": "pass"},
            {"name": "proposal_only", "status": "pass"},
            {"name": "temperature_zero", "status": "pass"},
        ]

    with patch(
        "src.decode_governance_executor.run_checkpoint_validators",
        side_effect=passing_checkpoints,
    ):
        result = execute_with_decode_governance(
            envelope,
            bridge_result=bridge,
            question=record.input_text,
            governance_ir=snapshot,
            decode_bundle=bundle,
            force_execute=True,
            generate_candidate=fake_generator,
        )
    runtime_label = _runtime_label_from_result(result)
    expected = str(record.label or "").strip().upper()
    aligned = (
        (expected == "COMPLIANT" and runtime_label == "COMPLIANT")
        or (expected == "VIOLATION" and runtime_label in {"VIOLATION", "BORDERLINE"})
        or (expected not in {"COMPLIANT", "VIOLATION"})
    )
    return {
        "status": "pass" if aligned else "fail",
        "view_id": record.view_id,
        "expected_label": expected,
        "runtime_label": runtime_label,
        "execution_status": result.get("status"),
        "label_parity": parity.get("status"),
    }
