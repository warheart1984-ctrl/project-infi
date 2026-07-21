"""Cortex self-tuning invariants — bounded parameter adjustment from turn evidence."""

from __future__ import annotations

from typing import Any

TUNING_ARTIFACT_VERSION = "1.1"
MAX_TUNING_HISTORY = 8
DEFAULT_THRESHOLDS: dict[str, float] = {
    "execution_overlap_min": 0.12,
    "focus_overlap_min": 0.10,
    "chain_advance_on_partial": 0.0,
}

DRIFT_LIMITS: dict[str, tuple[float, float]] = {
    "execution_overlap_min": (0.06, 0.18),
    "focus_overlap_min": (0.06, 0.16),
    "chain_advance_on_partial": (0.0, 1.0),
}

TUNABLE_INVARIANTS: tuple[str, ...] = (
    "execution_overlap_min",
    "focus_overlap_min",
    "chain_advance_on_partial",
)

ENV_CHANGE_FAIL_STREAK = 5
PERFORMANCE_METRIC_ID = "spark.performance.v1"
PERFORMANCE_ALPHA = 0.05


def compute_performance_score(
    artifacts: dict[str, Any],
    *,
    verification_trace: dict[str, Any] | None = None,
    operator_satisfaction: float | None = None,
) -> dict[str, Any]:
    """
    P = f(deliberation_success, operator_satisfaction, verification_pass_rate)
    Bounded [0, 1] objective for self-tuning.
    """
    decision = dict(artifacts.get("decision_object") or {})
    reflection = dict(artifacts.get("reflection_artifact") or {})
    execution = dict(artifacts.get("execution_artifact") or {})
    verification = dict(verification_trace or {})

    deliberation_success = 1.0 if decision.get("chosen_option") else 0.35
    if str(decision.get("commit_source") or "") == "llm":
        deliberation_success = min(1.0, deliberation_success + 0.15)

    attempts = list(verification.get("attempts") or [])
    if attempts:
        pass_rate = sum(1 for item in attempts if item.get("valid")) / len(attempts)
    elif verification.get("final_valid") is True:
        pass_rate = 1.0
    elif verification:
        pass_rate = 0.0
    else:
        pass_rate = 0.5 if str(execution.get("verification_status") or "") == "passed" else 0.4

    satisfaction = float(operator_satisfaction if operator_satisfaction is not None else 0.7)
    satisfaction = max(0.0, min(1.0, satisfaction))
    alignment_bonus = 0.1 if str(reflection.get("alignment") or "") == "aligned" else 0.0

    score = round(
        (0.35 * deliberation_success) + (0.40 * pass_rate) + (0.25 * satisfaction) + alignment_bonus,
        3,
    )
    score = max(0.0, min(1.0, score))
    return {
        "metric_id": PERFORMANCE_METRIC_ID,
        "score": score,
        "deliberation_success": round(deliberation_success, 3),
        "verification_pass_rate": round(pass_rate, 3),
        "operator_satisfaction": round(satisfaction, 3),
        "alignment_bonus": round(alignment_bonus, 3),
    }


def apply_performance_tuning(
    artifacts: dict[str, Any],
    *,
    prior_tuning: dict[str, Any] | None = None,
    performance: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """θ = θ + α * ∂P/∂θ with drift guard and env reset on failure streak."""
    perf = dict(performance or compute_performance_score(artifacts))
    tuned = run_self_tune_invariants(artifacts, prior_tuning=prior_tuning)
    score = float(perf.get("score") or 0.5)
    thresholds = dict(tuned.get("tuned_thresholds") or DEFAULT_THRESHOLDS)
    gradient = score - 0.5
    if gradient > 0:
        thresholds["focus_overlap_min"] = round(
            min(DRIFT_LIMITS["focus_overlap_min"][1], thresholds["focus_overlap_min"] + PERFORMANCE_ALPHA * gradient),
            3,
        )
    elif gradient < 0:
        thresholds["execution_overlap_min"] = round(
            max(DRIFT_LIMITS["execution_overlap_min"][0], thresholds["execution_overlap_min"] + PERFORMANCE_ALPHA * gradient),
            3,
        )
    thresholds, drift_guarded, drift_score = _apply_drift_guard(thresholds)
    tuned["tuned_thresholds"] = thresholds
    tuned["performance"] = perf
    tuned["performance_metric"] = PERFORMANCE_METRIC_ID
    tuned["drift_guarded"] = drift_guarded or tuned.get("drift_guarded")
    tuned["drift_score"] = drift_score
    return tuned


def load_tuned_thresholds(metadata: dict[str, Any] | None) -> dict[str, float]:
    stored = dict((metadata or {}).get("cortex_invariant_tuning") or {})
    thresholds = dict(DEFAULT_THRESHOLDS)
    tuned = stored.get("tuned_thresholds")
    if isinstance(tuned, dict):
        for key in TUNABLE_INVARIANTS:
            if key in tuned:
                thresholds[key] = float(tuned[key])
    return thresholds


def _apply_drift_guard(updated: dict[str, float]) -> tuple[dict[str, float], bool, float]:
    guarded = False
    drift_score = 0.0
    clamped = dict(updated)
    for key in TUNABLE_INVARIANTS:
        lo, hi = DRIFT_LIMITS.get(key, (0.0, 1.0))
        value = float(clamped.get(key, DEFAULT_THRESHOLDS[key]))
        bounded = max(lo, min(hi, value))
        if bounded != value:
            guarded = True
            drift_score += abs(value - bounded)
            clamped[key] = round(bounded, 3)
        drift_score += abs(bounded - DEFAULT_THRESHOLDS[key])
    return clamped, guarded, round(drift_score, 3)


def _append_tuning_history(
    prior: dict[str, Any],
    *,
    generation: int,
    tuned_thresholds: dict[str, float],
    trigger_verification: str,
    trigger_alignment: str,
) -> list[dict[str, Any]]:
    history = list(prior.get("tuning_history") or [])
    history.append(
        {
            "generation": generation,
            "tuned_thresholds": dict(tuned_thresholds),
            "trigger_verification": trigger_verification,
            "trigger_alignment": trigger_alignment,
        }
    )
    return history[-MAX_TUNING_HISTORY:]


def detect_tuning_env_change(prior_tuning: dict[str, Any] | None) -> bool:
    prior = dict(prior_tuning or {})
    if prior.get("operator_reset"):
        return True
    history = list(prior.get("tuning_history") or [])
    if len(history) < ENV_CHANGE_FAIL_STREAK:
        return False
    recent = history[-ENV_CHANGE_FAIL_STREAK:]
    fail_count = sum(
        1
        for item in recent
        if str(item.get("trigger_verification") or "") == "failed"
        or str(item.get("trigger_alignment") or "") == "misaligned"
    )
    return fail_count >= ENV_CHANGE_FAIL_STREAK


def reset_tuned_thresholds(*, reason: str) -> dict[str, Any]:
    return {
        "version": TUNING_ARTIFACT_VERSION,
        "tuning_generation": 1,
        "adjustments": [
            {
                "invariant_id": "env_reset",
                "parameter": "all",
                "delta": 0.0,
                "reason": reason,
            }
        ],
        "tuned_thresholds": dict(DEFAULT_THRESHOLDS),
        "tuning_history": [],
        "drift_guarded": False,
        "drift_score": 0.0,
        "trigger_verification": "reset",
        "trigger_alignment": "reset",
        "performance_metric": PERFORMANCE_METRIC_ID,
        "env_reset": True,
    }


def run_self_tune_invariants(
    artifacts: dict[str, Any],
    *,
    prior_tuning: dict[str, Any] | None = None,
    tuned_thresholds: dict[str, float] | None = None,
) -> dict[str, Any]:
    """Adjust bounded cortex thresholds from execution and reflection evidence."""
    prior = dict(prior_tuning or {})
    if detect_tuning_env_change(prior):
        return reset_tuned_thresholds(reason="Sustained verification/alignment fail streak or operator reset.")

    thresholds = dict(tuned_thresholds or DEFAULT_THRESHOLDS)
    generation = int(prior.get("tuning_generation") or 0) + 1

    execution = dict(artifacts.get("execution_artifact") or {})
    reflection = dict(artifacts.get("reflection_artifact") or {})
    planning = dict(artifacts.get("planning_artifact") or {})

    adjustments: list[dict[str, Any]] = []
    updated = dict(thresholds)

    verification = str(execution.get("verification_status") or "")
    if verification == "failed":
        updated["execution_overlap_min"] = round(max(0.06, thresholds["execution_overlap_min"] - 0.02), 3)
        adjustments.append(
            {
                "invariant_id": "execution_overlap_min",
                "parameter": "execution_overlap_min",
                "delta": -0.02,
                "reason": "Execution verification failed; relax overlap gate slightly.",
            }
        )
    elif verification == "passed" and thresholds["execution_overlap_min"] < DEFAULT_THRESHOLDS["execution_overlap_min"]:
        updated["execution_overlap_min"] = round(
            min(DEFAULT_THRESHOLDS["execution_overlap_min"], thresholds["execution_overlap_min"] + 0.01),
            3,
        )
        adjustments.append(
            {
                "invariant_id": "execution_overlap_min",
                "parameter": "execution_overlap_min",
                "delta": 0.01,
                "reason": "Stable passes; restore overlap gate toward default.",
            }
        )

    alignment = str(reflection.get("alignment") or "")
    if alignment == "misaligned":
        updated["focus_overlap_min"] = round(max(0.06, thresholds["focus_overlap_min"] - 0.02), 3)
        adjustments.append(
            {
                "invariant_id": "focus_overlap_min",
                "parameter": "focus_overlap_min",
                "delta": -0.02,
                "reason": "Reflection misaligned; relax focus visibility threshold.",
            }
        )

    if execution.get("rollback_applied") and planning.get("step_chains"):
        updated["chain_advance_on_partial"] = 1.0
        adjustments.append(
            {
                "invariant_id": "chain_advance_on_partial",
                "parameter": "chain_advance_on_partial",
                "delta": 1.0,
                "reason": "Rollback occurred; allow partial chain advance next turn.",
            }
        )
    elif verification == "passed":
        updated["chain_advance_on_partial"] = 0.0

    updated, drift_guarded, drift_score = _apply_drift_guard(updated)
    if drift_guarded:
        adjustments.append(
            {
                "invariant_id": "drift_guard",
                "parameter": "all",
                "delta": 0.0,
                "reason": "Drift guard clamped threshold adjustments to bounded limits.",
            }
        )

    history = _append_tuning_history(
        prior,
        generation=generation,
        tuned_thresholds=updated,
        trigger_verification=verification,
        trigger_alignment=alignment,
    )

    return {
        "version": TUNING_ARTIFACT_VERSION,
        "tuning_generation": generation,
        "adjustments": adjustments,
        "tuned_thresholds": updated,
        "tuning_history": history,
        "drift_guarded": drift_guarded,
        "drift_score": drift_score,
        "trigger_verification": verification,
        "trigger_alignment": alignment,
        "performance_metric": PERFORMANCE_METRIC_ID,
    }


def validate_tuning_artifact(artifact: dict[str, Any]) -> dict[str, Any]:
    issues: list[str] = []
    thresholds = artifact.get("tuned_thresholds")
    if not isinstance(thresholds, dict):
        issues.append("tuned_thresholds_not_object")
    adjustments = artifact.get("adjustments")
    if not isinstance(adjustments, list):
        issues.append("adjustments_not_list")
    generation = artifact.get("tuning_generation")
    if not isinstance(generation, int) or generation < 1:
        issues.append("invalid_tuning_generation")
    history = artifact.get("tuning_history")
    if not isinstance(history, list):
        issues.append("tuning_history_not_list")
    elif len(history) > MAX_TUNING_HISTORY:
        issues.append("tuning_history_too_long")
    if not isinstance(artifact.get("drift_guarded"), bool):
        issues.append("missing_drift_guarded")
    drift_score = artifact.get("drift_score")
    if not isinstance(drift_score, (int, float)):
        issues.append("missing_drift_score")
    return {"valid": not issues, "issues": issues}
