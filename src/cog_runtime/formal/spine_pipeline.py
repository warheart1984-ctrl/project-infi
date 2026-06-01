"""Formal Spine Doctrine — gated composition with halt-on-false."""

from __future__ import annotations

from typing import Any, Callable

SpineGate = Callable[[dict[str, Any]], bool]

SPINE_PIPELINE_STAGES: tuple[tuple[str, str], ...] = (
    ("wolf_check", "Wolf CoG OS substrate law and boot invariants"),
    ("aris_admit", "ARIS truth admission — non-copy gate"),
    ("jarvis_authorize", "Jarvis executive routing and policy posture"),
    ("cortex_execute", "Nova Cortex lobe composition and ledger"),
    ("speaking_emit", "Speaking Runtime user-visible output"),
)


def wolf_check(turn: dict[str, Any]) -> bool:
    governance = turn.get("governance") or turn.get("policy_status") or {}
    if isinstance(governance, dict) and governance.get("blocked"):
        return False
    return bool(turn.get("substrate_ok", True))


def aris_admit(turn: dict[str, Any]) -> bool:
    admission = turn.get("aris_admission") or turn.get("admission")
    if admission is None:
        return True
    if isinstance(admission, dict):
        status = str(admission.get("status") or "admitted").lower()
        if status in {"rejected", "blocked"}:
            return False
        if admission.get("non_copy_clause") and admission["non_copy_clause"].get("allowed") is False:
            return False
    return bool(admission)


def jarvis_authorize(turn: dict[str, Any]) -> bool:
    if turn.get("jarvis_blocked"):
        return False
    posture = str((turn.get("policy_status") or {}).get("posture") or turn.get("policy_posture") or "")
    if posture.lower() in {"blocked", "deny"}:
        return False
    return True


def cortex_execute(turn: dict[str, Any]) -> bool:
    if not turn.get("cognitive_runtime_enabled", True):
        return True
    return not bool(turn.get("cortex_halted"))


def speaking_emit(turn: dict[str, Any]) -> bool:
    if not turn.get("speaking_runtime_enabled") and not turn.get("companion_turn"):
        return True
    validation = turn.get("speaking_validation") or {}
    if validation and not validation.get("valid"):
        return bool(turn.get("speaking_wrap_on_fail", False))
    return True


def nova_cognize(turn: dict[str, Any]) -> bool:
    return cortex_execute(turn)


def speaking_produce(turn: dict[str, Any]) -> bool:
    return speaking_emit(turn)


SPINE_GATES: dict[str, SpineGate] = {
    "wolf_check": wolf_check,
    "aris_admit": aris_admit,
    "jarvis_authorize": jarvis_authorize,
    "cortex_execute": cortex_execute,
    "speaking_emit": speaking_emit,
    "nova_cognize": cortex_execute,
    "speaking_produce": speaking_emit,
}


def halt_receipt(
    *,
    halt_stage: str,
    trace: list[dict[str, Any]],
    pipeline_id: str = "nova.spine.v1",
    reason_codes: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "halted": True,
        "halt_stage": halt_stage,
        "trace": trace,
        "pipeline_id": pipeline_id,
        "reason_codes": list(reason_codes or [f"spine_halt:{halt_stage}"]),
        "status": "blocked",
    }


def evaluate_spine_pipeline(turn: dict[str, Any]) -> dict[str, Any]:
    """
    Spine(turn) = Wolf → ARIS → Jarvis → Cortex → Speaking.
    If any stage returns False, the turn halts at that stage.
    """
    halt_before_cortex = turn.get("halt_before_cortex")
    trace: list[dict[str, Any]] = []
    for stage_id, description in SPINE_PIPELINE_STAGES:
        if halt_before_cortex is True and stage_id in {"cortex_execute", "speaking_emit"}:
            continue
        if halt_before_cortex is False and stage_id in {"wolf_check", "aris_admit", "jarvis_authorize"}:
            continue
        gate = SPINE_GATES[stage_id]
        passed = bool(gate(turn))
        trace.append({"stage": stage_id, "description": description, "passed": passed})
        if not passed:
            return halt_receipt(halt_stage=stage_id, trace=trace)
    return {"halted": False, "halt_stage": None, "trace": trace, "pipeline_id": "nova.spine.v1"}
