"""Nova Intent Core — commitments, tensions, agency, closure (consult only)."""

# Mythic: Intent Core
# Engineering: IntentCoreEngine
from __future__ import annotations

from typing import Any

from src.cog_runtime.intent_agency_evidence import CLAIM_POSTURES

INTENT_MODULE_ID = "nova.intent"
INTENT_VERSION = "0.2"
INTENT_STAGES = ("orient", "tensions", "commitments", "conflicts", "closure", "persist")
MAX_COMMITMENTS = 8
MAX_TENSIONS = 6
MAX_HORIZON_GOALS = 4
MAX_PROTECTED_VALUES = 6
MAX_CONFLICTS = 4
MAX_DEFERRED = 3

COMMITMENT_STATUSES = frozenset(
    {"active", "resolved", "deferred", "superseded", "in_tension"}
)

TENSION_CATALOG: tuple[tuple[str, str, str], ...] = (
    ("safety", "exploration", "Prefer verified paths vs trying new approaches"),
    ("comfort", "growth", "Preserve stability vs stretch capability"),
    ("certainty", "curiosity", "Close decisions vs keep questions open"),
    ("present", "future", "Serve this turn vs long-horizon arc"),
    ("self", "others", "Operator intent vs external constraints"),
)

CONSTITUTIONAL_PROTECTED_VALUES: tuple[str, ...] = (
    "jarvis_executive_authority",
    "operator_safety",
    "proof_over_assertion",
    "identity_consistency",
)

PROVEN_COMMITMENT_MARKERS: tuple[str, ...] = (
    "narrative persistence",
    "session-boundary persistence",
    "identity_consistency",
)

OPPOSING_COMMITMENT_HINTS: tuple[tuple[tuple[str, ...], tuple[str, ...]], ...] = (
    (("safe", "verify", "defer", "cautious"), ("fast", "explore", "experimental", "risk")),
    (("minimal", "hold", "pause"), ("expand", "stretch", "ship", "accelerate")),
)

INTENT_INVARIANTS: tuple[dict[str, str], ...] = (
    {"id": "not_authority", "rule": "Intent Core does not route, authorize, or execute; Jarvis remains executive."},
    {"id": "not_planner", "rule": "Intent Core does not sequence tasks; Planning owns next_action."},
    {"id": "commitments_survive_story", "rule": "Active commitments persist when Narrative active_story changes."},
    {"id": "agency_not_memory", "rule": "Intent maintains commitments across interruptions; Memory recalls facts."},
    {"id": "consult_only", "rule": "Lobes consult intent; Intent does not override lobe outputs."},
    {"id": "unified_closure", "rule": "Arc, execution, and intent closure events are recorded in one artifact."},
)


def intent_module_spec() -> dict[str, Any]:
    from src.cog_runtime.capability_governance import cortex_module_capability_contract

    return {
        "id": INTENT_MODULE_ID,
        "version": INTENT_VERSION,
        "summary": (
            "Maintains commitments, tensions, claim posture, conflict resolution, and unified "
            "closure — agency that survives story change."
        ),
        **cortex_module_capability_contract(INTENT_MODULE_ID),
        "stages": list(INTENT_STAGES),
        "tension_catalog": [
            {"pole_a": a, "pole_b": b, "label": label} for a, b, label in TENSION_CATALOG
        ],
        "outputs": {
            "intent_artifact": {
                "active_commitments": "object[]",
                "protected_values": "string[]",
                "long_horizon_goals": "object[]",
                "current_tensions": "object[]",
                "commitment_conflicts": "object[]",
                "unified_closure": "object",
                "continuity_claim_posture": "string",
                "agency_note": "string",
            }
        },
        "invariants": [dict(item) for item in INTENT_INVARIANTS],
        "doc": "docs/runtime/NOVA_INTENT_CORE.md",
    }


def validate_intent_artifact(artifact: dict[str, Any]) -> dict[str, Any]:
    issues: list[str] = []
    for field in ("active_commitments", "protected_values", "long_horizon_goals", "current_tensions"):
        value = artifact.get(field)
        if not isinstance(value, list):
            issues.append(f"{field}_not_list")
    commitments = artifact.get("active_commitments")
    if isinstance(commitments, list) and len(commitments) > MAX_COMMITMENTS:
        issues.append("too_many_commitments")
    tensions = artifact.get("current_tensions")
    if isinstance(tensions, list) and len(tensions) > MAX_TENSIONS:
        issues.append("too_many_tensions")
    conflicts = artifact.get("commitment_conflicts")
    if conflicts is not None and not isinstance(conflicts, list):
        issues.append("commitment_conflicts_not_list")
    closure = artifact.get("unified_closure")
    if closure is not None and not isinstance(closure, dict):
        issues.append("unified_closure_not_object")
    posture = str(artifact.get("continuity_claim_posture") or "")
    if posture and posture not in CLAIM_POSTURES:
        issues.append("invalid_continuity_claim_posture")
    if not str(artifact.get("agency_note") or "").strip():
        issues.append("missing_agency_note")
    protected = artifact.get("protected_values")
    if isinstance(protected, list):
        for value in CONSTITUTIONAL_PROTECTED_VALUES:
            if value not in protected:
                issues.append(f"missing_protected_value:{value}")
    if isinstance(commitments, list):
        for item in commitments:
            if not isinstance(item, dict):
                continue
            status = str(item.get("status") or "active")
            if status not in COMMITMENT_STATUSES:
                issues.append(f"invalid_commitment_status:{status}")
            claim = str(item.get("claim_posture") or "")
            if claim and claim not in CLAIM_POSTURES:
                issues.append("invalid_commitment_claim_posture")
    return {"valid": not issues, "issues": issues}


def load_nova_intent(metadata: dict[str, Any] | None) -> dict[str, Any] | None:
    payload = dict(metadata or {}).get("nova_intent")
    if not isinstance(payload, dict):
        return None
    if not isinstance(payload.get("active_commitments"), list):
        return None
    return dict(payload)


def _infer_claim_posture(*, commitment: str, source: str) -> str:
    lowered = commitment.lower()
    if any(marker in lowered for marker in PROVEN_COMMITMENT_MARKERS):
        return "proven"
    if source == "operator":
        return "asserted"
    if "cross-machine" in lowered or "wolf reboot" in lowered or "metal" in lowered:
        return "asserted"
    return "asserted"


def _attach_claim_posture(item: dict[str, Any]) -> dict[str, Any]:
    payload = dict(item)
    if payload.get("claim_posture") in CLAIM_POSTURES:
        return payload
    payload["claim_posture"] = _infer_claim_posture(
        commitment=str(payload.get("commitment") or ""),
        source=str(payload.get("source") or ""),
    )
    return payload


def _horizon_goal_entries(
    *,
    arc: dict[str, Any],
    prior: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    seen: set[str] = set()
    if prior:
        for item in prior.get("long_horizon_goals") or []:
            if isinstance(item, dict):
                text = str(item.get("goal") or "").strip()
                posture = str(item.get("claim_posture") or "asserted")
            else:
                text = str(item).strip()
                posture = "asserted"
            if text and text not in seen:
                seen.add(text)
                entries.append({"goal": text[:160], "claim_posture": posture})
    root = str(arc.get("root_goal") or arc.get("goal") or "").strip()
    if root and root not in seen:
        entries.insert(0, {"goal": root[:160], "claim_posture": _infer_claim_posture(commitment=root, source="arc.root_goal")})
        seen.add(root)
    for subgoal in list(arc.get("subgoals") or [])[:2]:
        text = str(subgoal).strip()
        if text and text not in seen:
            entries.append({"goal": text[:160], "claim_posture": "asserted"})
            seen.add(text)
    return entries[:MAX_HORIZON_GOALS]


def _continuity_claim_posture(
    *,
    commitments: list[dict[str, Any]],
    horizon: list[dict[str, Any]],
) -> str:
    postures: list[str] = []
    for item in commitments:
        if isinstance(item, dict) and item.get("status") in {"active", "in_tension", "deferred"}:
            postures.append(str(item.get("claim_posture") or "asserted"))
    for item in horizon:
        if isinstance(item, dict):
            postures.append(str(item.get("claim_posture") or "asserted"))
    if not postures:
        return "asserted"
    if any(item == "rejected" for item in postures):
        return "rejected"
    if all(item == "proven" for item in postures):
        return "proven"
    if any(item == "proven" for item in postures):
        return "asserted"
    return "asserted"


def _commitments_oppose(left: str, right: str) -> bool:
    left_l = left.lower()
    right_l = right.lower()
    for group_a, group_b in OPPOSING_COMMITMENT_HINTS:
        left_a = any(token in left_l for token in group_a)
        left_b = any(token in left_l for token in group_b)
        right_a = any(token in right_l for token in group_a)
        right_b = any(token in right_l for token in group_b)
        if (left_a and right_b) or (left_b and right_a):
            return True
    return False


def _detect_commitment_conflicts(
    commitments: list[dict[str, Any]],
    *,
    current_tensions: list[dict[str, Any]],
    prior_narrative: dict[str, Any] | None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    updated = [dict(item) for item in commitments]
    conflicts: list[dict[str, Any]] = []
    active_indices = [
        index
        for index, item in enumerate(updated)
        if item.get("status") == "active"
    ]
    for left_index in active_indices:
        left = updated[left_index]
        left_text = str(left.get("commitment") or "")
        for right_index in active_indices:
            if right_index <= left_index:
                continue
            right = updated[right_index]
            right_text = str(right.get("commitment") or "")
            if not _commitments_oppose(left_text, right_text):
                continue
            conflict = {
                "commitment_a": left_text[:160],
                "commitment_b": right_text[:160],
                "resolution": "in_tension",
                "reason": "Opposing commitment hints detected; both remain visible under consult.",
            }
            conflicts.append(conflict)
            left["status"] = "in_tension"
            left["in_tension_with"] = [right_text[:160]]
            right["status"] = "in_tension"
            right["in_tension_with"] = [left_text[:160]]

    primary_pull = str((current_tensions[0] or {}).get("pull") or "") if current_tensions else ""
    prior_story = str((prior_narrative or {}).get("active_story") or "").lower()
    if prior_story and primary_pull == "safety" and any(token in prior_story for token in ("explor", "research", "experiment")):
        conflicts.append(
            {
                "type": "story_intent",
                "resolution": "in_tension",
                "reason": "Prior story pulls exploration while current tension pull favors safety.",
                "story_excerpt": prior_story[:120],
                "pull": primary_pull,
            }
        )

    return updated, conflicts[:MAX_CONFLICTS]


def _apply_deferral(
    commitments: list[dict[str, Any]],
    *,
    conflicts: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    if not conflicts:
        return commitments
    updated = [dict(item) for item in commitments]
    active = [item for item in updated if item.get("status") == "active"]
    if len(active) <= 3:
        return updated
    defer_candidates = [
        item
        for item in active
        if item.get("source") not in {"operator", "planning.next_action"}
    ][:MAX_DEFERRED]
    for item in defer_candidates:
        item["status"] = "deferred"
        item["defer_reason"] = "Deferred during commitment overload while higher-priority items remain active."
    return updated


def synthesize_unified_closure(
    *,
    arc: dict[str, Any],
    planning: dict[str, Any],
    execution: dict[str, Any],
    commitments: list[dict[str, Any]],
) -> dict[str, Any]:
    layers: list[dict[str, Any]] = []
    next_action = str(planning.get("next_action") or "").strip()
    execution_complete = bool(execution.get("execution_complete"))
    verification = str(execution.get("verification_status") or execution.get("status") or "")
    arc_closure = str(arc.get("goal_closure_status") or "open")

    if execution_complete and next_action:
        layers.append(
            {
                "layer": "execution",
                "status": verification or "complete",
                "action": next_action[:160],
            }
        )
    if arc_closure in {"subgoals_closed", "parent_closed"}:
        layers.append({"layer": "arc", "status": arc_closure, "goal": str(arc.get("root_goal") or arc.get("goal") or "")[:160]})
    resolved = [
        str(item.get("commitment") or "")
        for item in commitments
        if isinstance(item, dict) and item.get("status") == "resolved"
    ]
    if resolved:
        layers.append({"layer": "intent", "status": "resolved", "commitments": resolved[:4]})

    unified = bool(layers) and (
        (execution_complete and bool(resolved))
        or arc_closure in {"subgoals_closed", "parent_closed"}
    )
    summary = "No unified closure this turn."
    if unified:
        summary = f"Closed across {len(layers)} layer(s): " + ", ".join(str(item.get("layer")) for item in layers)
    elif layers:
        summary = f"Partial closure across {len(layers)} layer(s)."

    return {
        "unified": unified,
        "layers": layers,
        "summary": summary[:220],
    }


def _infer_tensions(
    *,
    deliberation: dict[str, Any],
    reflection: dict[str, Any],
    arc: dict[str, Any],
    frame_kind: str,
) -> list[dict[str, Any]]:
    tensions: list[dict[str, Any]] = []
    alternatives = list(deliberation.get("alternatives") or [])
    alignment = str(reflection.get("alignment") or "")
    goal_type = str(arc.get("goal_type") or "general")

    if len(alternatives) >= 2 or frame_kind == "decision":
        tensions.append(
            {
                "poles": ["certainty", "curiosity"],
                "pull": "certainty",
                "reason": "Decision frame with competing options requires closure vs exploration.",
            }
        )
    if goal_type in {"exploration", "research"} or frame_kind in {"design", "implementation"}:
        tensions.append(
            {
                "poles": ["safety", "exploration"],
                "pull": "exploration",
                "reason": f"Arc goal type '{goal_type}' pulls toward exploration under governance.",
            }
        )
    if alignment in {"partial", "misaligned"}:
        tensions.append(
            {
                "poles": ["comfort", "growth"],
                "pull": "growth",
                "reason": "Reflection gaps pull toward growth-oriented delivery adjustment.",
            }
        )
    if arc.get("turn_count", 0) and arc.get("turn_count", 0) > 1:
        tensions.append(
            {
                "poles": ["present", "future"],
                "pull": "future",
                "reason": "Multi-turn arc maintains long-horizon pull beyond this turn.",
            }
        )
    if not tensions:
        tensions.append(
            {
                "poles": ["present", "future"],
                "pull": "present",
                "reason": "Default turn tension: serve immediate operator intent.",
            }
        )
    return tensions[:MAX_TENSIONS]


def _merge_commitments(
    *,
    prior: dict[str, Any] | None,
    planning: dict[str, Any],
    reflection: dict[str, Any],
    execution: dict[str, Any],
) -> list[dict[str, Any]]:
    merged: list[dict[str, Any]] = []
    seen: set[str] = set()

    if prior:
        for item in prior.get("active_commitments") or []:
            if not isinstance(item, dict):
                continue
            text = str(item.get("commitment") or "").strip()
            if text and text not in seen and item.get("status") not in {"resolved", "superseded"}:
                seen.add(text)
                merged.append(_attach_claim_posture(dict(item)))

    next_action = str(planning.get("next_action") or "").strip()
    if next_action and next_action not in seen:
        merged.append(
            _attach_claim_posture(
                {
                    "commitment": next_action[:160],
                    "status": "active",
                    "source": "planning.next_action",
                }
            )
        )
        seen.add(next_action)

    for adjustment in reflection.get("adjustments") or []:
        text = str(adjustment).strip()
        if text and text not in seen:
            merged.append(
                _attach_claim_posture(
                    {"commitment": text[:160], "status": "active", "source": "reflection.adjustment"}
                )
            )
            seen.add(text)

    if execution.get("execution_complete") and next_action:
        for item in merged:
            if item.get("commitment") == next_action:
                item["status"] = "resolved"
                item["closure_source"] = "execution.complete"

    return merged[:MAX_COMMITMENTS]


def _build_agency_note(
    *,
    commitments: list[dict[str, Any]],
    tensions: list[dict[str, Any]],
    horizon: list[dict[str, Any]],
    conflicts: list[dict[str, Any]],
    closure: dict[str, Any],
) -> str:
    active = [c for c in commitments if c.get("status") in {"active", "in_tension", "deferred"}]
    if not active and not horizon:
        return "Hold agency across interruptions under Jarvis authority."
    pull = tensions[0]["pull"] if tensions else "present"
    if horizon:
        goal = str(horizon[0].get("goal") or "")
    else:
        goal = str(active[0]["commitment"])
    note = (
        f"Still committed to '{goal[:80]}' while pulled toward {pull} "
        f"({len(active)} active commitment(s))."
    )
    if conflicts:
        note += f" {len(conflicts)} conflict(s) visible."
    if closure.get("unified"):
        note += " Unified closure recorded."
    return note[:220]


def run_intent_turn(
    *,
    cog_session: Any,
    prior_intent: dict[str, Any] | None = None,
    prior_narrative: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Synthesize intent artifact from cortex outputs — consult layer, not authority."""
    artifacts = dict(getattr(cog_session, "artifacts", {}) or {})
    arc = dict(artifacts.get("cognitive_arc") or {})
    deliberation = dict(artifacts.get("decision_object") or {})
    reflection = dict(artifacts.get("reflection_artifact") or {})
    planning = dict(artifacts.get("planning_artifact") or {})
    execution = dict(artifacts.get("execution_artifact") or {})
    prior = dict(prior_intent or {})
    frame_kind = str(getattr(cog_session, "frame_kind", "") or "general")

    current_tensions = _infer_tensions(
        deliberation=deliberation,
        reflection=reflection,
        arc=arc,
        frame_kind=frame_kind,
    )
    active_commitments = _merge_commitments(
        prior=prior or None,
        planning=planning,
        reflection=reflection,
        execution=execution,
    )
    active_commitments, commitment_conflicts = _detect_commitment_conflicts(
        active_commitments,
        current_tensions=current_tensions,
        prior_narrative=prior_narrative,
    )
    active_commitments = _apply_deferral(active_commitments, conflicts=commitment_conflicts)
    long_horizon_goals = _horizon_goal_entries(arc=arc, prior=prior or None)
    protected_values = list(dict.fromkeys(list(CONSTITUTIONAL_PROTECTED_VALUES)))[:MAX_PROTECTED_VALUES]
    unified_closure = synthesize_unified_closure(
        arc=arc,
        planning=planning,
        execution=execution,
        commitments=active_commitments,
    )
    continuity_claim_posture = _continuity_claim_posture(
        commitments=active_commitments,
        horizon=long_horizon_goals,
    )
    agency_note = _build_agency_note(
        commitments=active_commitments,
        tensions=current_tensions,
        horizon=long_horizon_goals,
        conflicts=commitment_conflicts,
        closure=unified_closure,
    )

    intent_artifact = {
        "version": INTENT_VERSION,
        "active_commitments": active_commitments,
        "protected_values": protected_values,
        "long_horizon_goals": long_horizon_goals,
        "current_tensions": current_tensions,
        "commitment_conflicts": commitment_conflicts,
        "unified_closure": unified_closure,
        "continuity_claim_posture": continuity_claim_posture,
        "agency_note": agency_note,
        "stages_completed": list(INTENT_STAGES),
    }
    validation = validate_intent_artifact(intent_artifact)
    if not validation["valid"]:
        raise ValueError(f"intent turn invalid: {validation['issues']}")
    return intent_artifact


def persist_nova_intent(session, artifact: dict[str, Any] | None) -> None:
    if session is None or not isinstance(artifact, dict):
        return
    metadata = getattr(session, "metadata", None)
    if not isinstance(metadata, dict):
        return
    metadata["nova_intent"] = dict(artifact)


def intent_context_for_lobes(intent: dict[str, Any] | None) -> dict[str, Any]:
    """Read-only consult surface for Planning, Deliberation, Narrative."""
    payload = dict(intent or {})
    if not payload:
        return {}
    return {
        "intent_commitments": list(payload.get("active_commitments") or []),
        "intent_tensions": list(payload.get("current_tensions") or []),
        "intent_horizon_goals": list(payload.get("long_horizon_goals") or []),
        "intent_protected_values": list(payload.get("protected_values") or []),
        "intent_agency_note": payload.get("agency_note"),
        "intent_conflicts": list(payload.get("commitment_conflicts") or []),
        "intent_claim_posture": payload.get("continuity_claim_posture"),
    }
