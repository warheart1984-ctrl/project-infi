"""Execution Runtime — Bind → Execute → Verify → Recover → Rollback → Report."""

from __future__ import annotations

import re
from typing import Any

from src.cog_runtime.base import CogRuntimeSession, runtime_spec_template
from src.cog_runtime.capability_governance import lobe_capability_contract

EXECUTION_RUNTIME_ID = "cognitive.execution"
EXECUTION_RUNTIME_VERSION = "1.2"
EXECUTION_STAGES = ("bind", "execute", "verify", "recover", "rollback", "report")
REQUIRED_TURN_STAGES = ("bind", "execute", "verify", "report")
WORD_RE = re.compile(r"[A-Za-z0-9']{3,}")

EXECUTION_INVARIANTS: tuple[dict[str, str], ...] = (
    {"id": "planning_bound", "rule": "Execution binds only to an explicit planning next_action."},
    {"id": "non_competing", "rule": "Execution reports outcomes; Jarvis retains authority for side effects."},
    {"id": "verify_before_report", "rule": "Report follows verify stage in ledger order."},
    {"id": "recovery_before_rollback", "rule": "Rollback applies only after recovery attempt on failed verification."},
    {"id": "safe_rollback", "rule": "Rollback skips partial passes, same targets, and capped repeat rollbacks."},
)


def execution_runtime_spec() -> dict[str, Any]:
    return runtime_spec_template(
        runtime_id=EXECUTION_RUNTIME_ID,
        version=EXECUTION_RUNTIME_VERSION,
        summary="Execute planned actions with tiered recovery and safe rollback policy.",
        stages=EXECUTION_STAGES,
        required_turn_stages=REQUIRED_TURN_STAGES,
        invariants=EXECUTION_INVARIANTS,
        inputs={
            "planning_artifact": "object",
            "focus_artifact": "object",
            "decision_object": "object",
            "reflection_artifact": "object",
            "cognitive_arc": "object",
            "frame_kind": "string",
            "speak_body": "string",
            "tuned_thresholds": "object",
        },
        outputs={
            "execution_artifact": {
                "bound_action": "string",
                "executed_steps": "string[]",
                "verification_status": "passed|partial|failed",
                "recovery_paths": "object[]",
                "recovery_action": "string",
                "recovery_tier": "number",
                "recovered": "boolean",
                "rollback_target": "string",
                "rollback_applied": "boolean",
                "rollback_policy": "string",
                "rollback_safe": "boolean",
                "report": "string",
                "execution_complete": "boolean",
            }
        },
        doc="docs/runtime/NOVA_CORTEX.md",
        **lobe_capability_contract(EXECUTION_RUNTIME_ID),
    )


def validate_execution_artifact(artifact: dict[str, Any]) -> dict[str, Any]:
    issues: list[str] = []
    if not str(artifact.get("bound_action") or "").strip():
        issues.append("missing_bound_action")
    steps = artifact.get("executed_steps")
    if not isinstance(steps, list) or not steps:
        issues.append("missing_executed_steps")
    status = str(artifact.get("verification_status") or "")
    if status not in {"passed", "partial", "failed"}:
        issues.append("invalid_verification_status")
    if not isinstance(artifact.get("recovery_paths"), list):
        issues.append("recovery_paths_not_list")
    recovery_tier = artifact.get("recovery_tier")
    if not isinstance(recovery_tier, int) or recovery_tier < 0:
        issues.append("invalid_recovery_tier")
    if not str(artifact.get("report") or "").strip():
        issues.append("missing_report")
    if not isinstance(artifact.get("execution_complete"), bool):
        issues.append("missing_execution_complete")
    if not isinstance(artifact.get("recovered"), bool):
        issues.append("missing_recovered")
    if not isinstance(artifact.get("rollback_applied"), bool):
        issues.append("missing_rollback_applied")
    policy = str(artifact.get("rollback_policy") or "")
    if not policy:
        issues.append("missing_rollback_policy")
    if not isinstance(artifact.get("rollback_safe"), bool):
        issues.append("missing_rollback_safe")
    return {"valid": not issues, "issues": issues}


def should_activate_execution(
    planning_artifact: dict[str, Any] | None,
    *,
    companion_turn: bool = False,
) -> bool:
    planning = dict(planning_artifact or {})
    if planning.get("execution_handoff") is True:
        return True
    if companion_turn and planning.get("next_action"):
        return True
    return bool(planning.get("next_action"))


def _token_overlap(left: str, right: str) -> float:
    left_tokens = set(WORD_RE.findall(left.lower()))
    right_tokens = set(WORD_RE.findall(right.lower()))
    if not left_tokens or not right_tokens:
        return 0.0
    return len(left_tokens & right_tokens) / max(len(left_tokens), 1)


def _normalize_action(text: str) -> str:
    return " ".join(WORD_RE.findall(str(text or "").lower()))


def _verify_execution(
    *,
    bound_action: str,
    speak_body: str,
    focus_artifact: dict[str, Any],
    checkpoints: list[str],
    tuned_thresholds: dict[str, float] | None = None,
) -> tuple[str, list[str]]:
    thresholds = dict(tuned_thresholds or {})
    action_min = float(thresholds.get("execution_overlap_min", 0.12))
    focus_min = float(thresholds.get("focus_overlap_min", 0.10))

    gaps: list[str] = []
    body = str(speak_body or "").strip()
    if not body:
        return "failed", ["empty_delivery"]

    action_score = _token_overlap(body, bound_action)
    focus_score = _token_overlap(body, str(focus_artifact.get("primary_focus") or ""))
    if action_score < action_min:
        gaps.append("planned_action_not_visible")
    if focus_score < focus_min:
        gaps.append("focus_not_visible")

    for checkpoint in checkpoints[:2]:
        checkpoint_tokens = set(WORD_RE.findall(checkpoint.lower()))
        body_tokens = set(WORD_RE.findall(body.lower()))
        if checkpoint_tokens and not (checkpoint_tokens & body_tokens):
            gaps.append(f"checkpoint_missed:{checkpoint[:40]}")

    if not gaps:
        return "passed", gaps
    if action_score >= action_min * 0.65 or focus_score >= focus_min * 0.65:
        return "partial", gaps
    return "failed", gaps


def _build_recovery_action(gaps: list[str], *, bound_action: str, focus: dict[str, Any]) -> str:
    if "planned_action_not_visible" in gaps:
        return f"Restate planned action in opening lines: {bound_action}"
    if "focus_not_visible" in gaps:
        primary = focus.get("primary_focus") or "turn focus"
        return f"Lead with focus '{primary}' before expanding the answer."
    if any(gap.startswith("checkpoint_missed:") for gap in gaps):
        return "Satisfy planning checkpoints before expanding scope."
    return "Tighten delivery to planned action and focus before adding detail."


def _build_recovery_paths(
    gaps: list[str],
    *,
    bound_action: str,
    focus: dict[str, Any],
    checkpoints: list[str],
) -> list[dict[str, Any]]:
    paths: list[dict[str, Any]] = []
    primary = _build_recovery_action(gaps, bound_action=bound_action, focus=focus)
    paths.append({"tier": 1, "action": primary, "kind": "restate"})

    missed = [gap.split(":", 1)[-1] for gap in gaps if gap.startswith("checkpoint_missed:")]
    if missed:
        paths.append(
            {
                "tier": 2,
                "action": f"Close checkpoint gaps: {missed[0][:80]}",
                "kind": "checkpoint",
            }
        )

    secondary = str(focus.get("secondary_focus") or focus.get("primary_focus") or "").strip()
    if secondary and "focus_not_visible" in gaps:
        paths.append(
            {
                "tier": 3,
                "action": f"Anchor reply to secondary focus: {secondary[:80]}",
                "kind": "focus_anchor",
            }
        )

    paths.append(
        {
            "tier": len(paths) + 1,
            "action": "Deliver a minimal focus-aligned answer before adding detail.",
            "kind": "fallback",
        }
    )
    return paths[:4]


def _resolve_rollback_target(
    planning: dict[str, Any],
    cognitive_arc: dict[str, Any] | None,
) -> str:
    arc = dict(cognitive_arc or {})
    prior = str(arc.get("prior_next_action") or "").strip()
    if prior:
        return prior
    chains = list(planning.get("step_chains") or [])
    if len(chains) > 1:
        fallback_steps = list(chains[1].get("steps") or [])
        if fallback_steps:
            return str(fallback_steps[0])
    steps = list(planning.get("steps") or [])
    if len(steps) > 1:
        return str(steps[1])
    return str(planning.get("next_action") or "Deliver a clear, focus-aligned reply.")


def _evaluate_rollback_policy(
    *,
    verification_status: str,
    speak_body: str,
    bound_action: str,
    rollback_target: str,
    cognitive_arc: dict[str, Any] | None,
    recovery_paths: list[dict[str, Any]],
    recovered: bool,
) -> tuple[bool, str, bool]:
    if verification_status == "passed":
        return False, "skipped_passed", True
    if verification_status == "partial":
        return False, "skipped_partial", True
    if not rollback_target.strip():
        return False, "denied_no_target", True
    if _normalize_action(rollback_target) == _normalize_action(bound_action):
        return False, "skipped_same_target", False

    arc = dict(cognitive_arc or {})
    if arc.get("prior_rollback_applied"):
        return False, "denied_rollback_cap", True

    if not str(speak_body or "").strip():
        return True, "applied_pre_reply", True

    if recovered:
        return False, "skipped_recovered", True

    if len(recovery_paths) >= 2:
        return True, "applied_post_reply", True
    return False, "skipped_recovery_pending", True


def run_execution_turn(
    *,
    planning_artifact: dict[str, Any],
    focus_artifact: dict[str, Any] | None = None,
    decision_object: dict[str, Any] | None = None,
    reflection_artifact: dict[str, Any] | None = None,
    cognitive_arc: dict[str, Any] | None = None,
    frame_kind: str = "general",
    user_message: str = "",
    speak_body: str = "",
    tuned_thresholds: dict[str, float] | None = None,
) -> tuple[dict[str, Any], CogRuntimeSession]:
    session = CogRuntimeSession(
        runtime_id=EXECUTION_RUNTIME_ID,
        user_message=user_message,
        context={"frame_kind": frame_kind},
        required_stages=REQUIRED_TURN_STAGES,
        stage_order=EXECUTION_STAGES,
    )

    planning = dict(planning_artifact or {})
    focus = dict(focus_artifact or {})
    decision = dict(decision_object or {})
    reflection = dict(reflection_artifact or {})

    bound_action = str(planning.get("next_action") or "").strip()
    if not bound_action:
        bound_action = str((planning.get("steps") or ["Deliver focus-aligned reply"])[0])

    session.start_stage("bind", {"planning_step": planning.get("arc_step")})
    session.end_stage(
        "bind",
        {
            "bound_action": bound_action,
            "checkpoints": list(planning.get("checkpoints") or []),
            "active_chain_id": planning.get("active_chain_id"),
        },
    )

    executed_steps: list[str] = [bound_action]
    active_chain = planning.get("active_chain") or {}
    for step in list(active_chain.get("steps") or planning.get("steps") or [])[1:3]:
        text = str(step).strip()
        if text and text not in executed_steps:
            executed_steps.append(text)
    if decision.get("chosen_option"):
        executed_steps.append(f"Honor decision: {decision['chosen_option']}")

    session.start_stage("execute", {"bound_action": bound_action})
    session.end_stage("execute", {"executed_steps": executed_steps})

    verification_status, gaps = _verify_execution(
        bound_action=bound_action,
        speak_body=speak_body,
        focus_artifact=focus,
        checkpoints=list(planning.get("checkpoints") or []),
        tuned_thresholds=tuned_thresholds,
    )
    if not speak_body and reflection.get("alignment") == "aligned":
        verification_status = "partial"
        gaps = gaps or ["pre_reply_execution"]

    session.start_stage("verify", {"speak_body_len": len(speak_body)})
    session.end_stage("verify", {"verification_status": verification_status, "gaps": gaps})

    recovery_paths: list[dict[str, Any]] = []
    recovery_action = ""
    recovery_tier = 0
    recovered = False
    rollback_target = ""
    rollback_applied = False
    rollback_policy = "skipped_passed" if verification_status == "passed" else ""
    rollback_safe = True

    if verification_status != "passed":
        recovery_paths = _build_recovery_paths(
            gaps,
            bound_action=bound_action,
            focus=focus,
            checkpoints=list(planning.get("checkpoints") or []),
        )
        recovery_action = str(recovery_paths[0]["action"])
        recovery_tier = int(recovery_paths[0]["tier"])
        session.start_stage("recover", {"gaps": gaps, "paths": len(recovery_paths)})
        session.end_stage(
            "recover",
            {"recovery_action": recovery_action, "recovery_paths": recovery_paths},
        )
        if speak_body and verification_status == "partial":
            recovered = True

        rollback_target = _resolve_rollback_target(planning, cognitive_arc)
        rollback_applied, rollback_policy, rollback_safe = _evaluate_rollback_policy(
            verification_status=verification_status,
            speak_body=speak_body,
            bound_action=bound_action,
            rollback_target=rollback_target,
            cognitive_arc=cognitive_arc,
            recovery_paths=recovery_paths,
            recovered=recovered,
        )
        session.start_stage("rollback", {"rollback_target": rollback_target, "policy": rollback_policy})
        session.end_stage(
            "rollback",
            {
                "rollback_applied": rollback_applied,
                "rollback_target": rollback_target,
                "rollback_policy": rollback_policy,
                "rollback_safe": rollback_safe,
            },
        )
        if rollback_applied:
            bound_action = rollback_target
            if rollback_target not in executed_steps:
                executed_steps = [rollback_target] + executed_steps[:2]

    execution_complete = verification_status == "passed" or recovered
    report = (
        f"Executed '{bound_action}' with {verification_status} verification "
        f"under {frame_kind} frame."
    )
    if recovery_action:
        report += f" Recovery tier {recovery_tier}: {recovery_action}"
    if rollback_applied:
        report += f" Rollback ({rollback_policy}) to: {rollback_target}."
    elif rollback_policy and rollback_policy not in {"skipped_passed"}:
        report += f" Rollback skipped ({rollback_policy})."
    if gaps:
        report += f" Gaps: {', '.join(gaps[:3])}."

    session.start_stage("report", {"verification_status": verification_status})
    session.end_stage(
        "report",
        {
            "report": report,
            "execution_complete": execution_complete,
            "recovered": recovered,
            "rollback_applied": rollback_applied,
        },
    )

    execution_artifact = {
        "bound_action": bound_action,
        "executed_steps": executed_steps,
        "verification_status": verification_status,
        "recovery_paths": recovery_paths,
        "recovery_action": recovery_action,
        "recovery_tier": recovery_tier,
        "recovered": recovered,
        "rollback_target": rollback_target,
        "rollback_applied": rollback_applied,
        "rollback_policy": rollback_policy,
        "rollback_safe": rollback_safe,
        "report": report,
        "execution_complete": execution_complete,
    }

    validation = validate_execution_artifact(execution_artifact)
    if not validation["valid"]:
        raise ValueError(f"execution turn invalid: {validation['issues']}")
    turn_validation = session.validate_turn()
    if not turn_validation["valid"]:
        raise ValueError(f"execution ledger invalid: {turn_validation['issues']}")

    return execution_artifact, session


def merge_post_reply_execution(
    execution_artifact: dict[str, Any],
    *,
    speak_body: str,
    planning_artifact: dict[str, Any] | None = None,
    focus_artifact: dict[str, Any] | None = None,
    cognitive_arc: dict[str, Any] | None = None,
    tuned_thresholds: dict[str, float] | None = None,
) -> dict[str, Any]:
    """Re-verify execution after the final reply is available."""
    planning = dict(planning_artifact or {})
    bound_action = str(execution_artifact.get("bound_action") or planning.get("next_action") or "")
    status, gaps = _verify_execution(
        bound_action=bound_action,
        speak_body=speak_body,
        focus_artifact=dict(focus_artifact or {}),
        checkpoints=list(planning.get("checkpoints") or []),
        tuned_thresholds=tuned_thresholds,
    )
    merged = dict(execution_artifact)
    merged["verification_status"] = status
    merged["execution_complete"] = status == "passed"

    recovery_paths = _build_recovery_paths(
        gaps,
        bound_action=bound_action,
        focus=dict(focus_artifact or {}),
        checkpoints=list(planning.get("checkpoints") or []),
    )
    merged["recovery_paths"] = recovery_paths
    merged["recovery_tier"] = int(recovery_paths[0]["tier"]) if recovery_paths else 0
    merged["recovery_action"] = str(recovery_paths[0]["action"]) if recovery_paths else ""

    recovered = False
    if status == "partial":
        recovered = True
        merged["recovered"] = True
    elif status == "passed":
        merged["recovered"] = False
        merged["rollback_policy"] = "skipped_passed"
        merged["rollback_applied"] = False
        merged["rollback_safe"] = True
    else:
        merged["recovered"] = False

    if status == "failed" and not merged.get("rollback_applied"):
        rollback_target = _resolve_rollback_target(planning, cognitive_arc)
        rollback_applied, rollback_policy, rollback_safe = _evaluate_rollback_policy(
            verification_status=status,
            speak_body=speak_body,
            bound_action=bound_action,
            rollback_target=rollback_target,
            cognitive_arc=cognitive_arc,
            recovery_paths=recovery_paths,
            recovered=recovered,
        )
        merged["rollback_target"] = rollback_target
        merged["rollback_applied"] = rollback_applied
        merged["rollback_policy"] = rollback_policy
        merged["rollback_safe"] = rollback_safe
        if rollback_applied:
            merged["bound_action"] = rollback_target

    merged["execution_complete"] = status == "passed" or merged.get("recovered", False)
    merged["report"] = (
        f"Post-reply verification {status} for '{bound_action}'."
        + (f" Gaps: {', '.join(gaps[:3])}." if gaps else "")
    )
    return merged
