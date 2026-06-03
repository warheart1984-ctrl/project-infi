"""Sovereign "God Brain" orchestration for Jarvis turns.

The God Brain is not a separate heavyweight model. It is a turn orchestrator
that decides how Jarvis should use its current mode, specialist council,
evidence, and policy posture before the final model answer is generated.
"""

# Mythic: God Brain
# Engineering: GodBrainEngine
from __future__ import annotations

from src.specialist_registry import SPECIALIST_DEFINITIONS, normalize_requested_specialists


SUPPORTED_RESPONSE_MODES = {"tiny", "fast", "think", "debug", "builder", "research", "operator"}


MODE_STRATEGIES = {
    "tiny": {
        "strategy_id": "gentle_presence",
        "strategy_label": "Gentle Presence",
        "summary": "Stay brief, warm, and present-focused while offering one useful next thought.",
        "fallback_label": "Companion",
        "fallback_purpose": "notice what matters and respond with one clear, calming reflection",
    },
    "fast": {
        "strategy_id": "snap_judgment",
        "strategy_label": "Snap Judgment",
        "summary": "Move quickly, keep context lean, and answer with the clearest useful line.",
        "fallback_label": "Rapid Resolver",
        "fallback_purpose": "cut to the answer quickly without losing the thread",
    },
    "think": {
        "strategy_id": "council_deliberation",
        "strategy_label": "Council Deliberation",
        "summary": "Gather context, let the council compare angles, then merge into one grounded answer.",
        "fallback_label": "Deliberator",
        "fallback_purpose": "compare options carefully before committing to one answer",
    },
    "debug": {
        "strategy_id": "fault_isolation",
        "strategy_label": "Fault Isolation Council",
        "summary": "Trace evidence, isolate the likeliest break point, and push toward a proof step.",
        "fallback_label": "Root Cause Hunter",
        "fallback_purpose": "hunt for the strongest failure signal and the fastest proof step",
    },
    "builder": {
        "strategy_id": "shipping_sequencer",
        "strategy_label": "Build Sequencer",
        "summary": "Turn the request into the smallest working slice and sequence the next build steps.",
        "fallback_label": "Shipwright",
        "fallback_purpose": "shape the smallest working slice and sequence the next build step",
    },
    "research": {
        "strategy_id": "evidence_synthesis",
        "strategy_label": "Evidence Synthesis Council",
        "summary": "Weight current evidence, compare options, and answer with honest uncertainty.",
        "fallback_label": "Evidence Mapper",
        "fallback_purpose": "map competing evidence and converge on the strongest conclusion",
    },
    "operator": {
        "strategy_id": "control_room",
        "strategy_label": "Control Room",
        "summary": "Inspect local state, stay inside guardrails, and pick the safest operator move.",
        "fallback_label": "Systems Operator",
        "fallback_purpose": "ground every move in local state, approvals, and verification",
    },
}


ACTION_BIAS_LABELS = {
    "answer_directly": "answer directly",
    "deliberate_then_answer": "deliberate then answer",
    "isolate_then_verify": "isolate then verify",
    "sequence_smallest_working_slice": "sequence the smallest working slice",
    "synthesize_current_evidence": "synthesize current evidence",
    "inspect_local_artifacts": "inspect local artifacts",
    "verify_then_act": "verify then act",
    "guard_and_verify": "guard and verify",
    "await_operator_approval": "await operator approval",
    "verify_after_action": "verify after action",
    "tool_first_resolution": "resolve through the tool path first",
}


def _normalize_response_mode(value: str | None) -> str:
    cleaned = str(value or "fast").strip().lower()
    return cleaned if cleaned in SUPPORTED_RESPONSE_MODES else "fast"


def _clip(text: str | None, limit: int = 180) -> str:
    normalized = " ".join(str(text or "").split()).strip()
    if len(normalized) <= limit:
        return normalized
    return normalized[: limit - 3].rstrip() + "..."


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _confidence_label(value: float) -> str:
    if value >= 0.82:
        return "high confidence"
    if value >= 0.62:
        return "steady confidence"
    if value >= 0.45:
        return "calibrating"
    return "low confidence"


def _disagreement_label(value: float) -> str:
    if value >= 0.72:
        return "high disagreement"
    if value >= 0.42:
        return "some disagreement"
    return "low disagreement"


def _build_arbiter_member(response_mode: str, current_goal: str | None) -> dict:
    mode_profile = MODE_STRATEGIES[response_mode]
    return {
        "id": "sovereign_core",
        "label": "Sovereign Core",
        "role": "arbiter",
        "source": "god_brain",
        "purpose": (
            f"hold the whole turn together around {mode_profile['strategy_label'].lower()} "
            f"while protecting the operator goal: {_clip(current_goal or 'make forward progress', 100)}"
        ),
    }


def _build_specialist_members(
    response_mode: str,
    specialist_profile: dict | None,
    requested_specialists=None,
) -> list[dict]:
    members: list[dict] = []
    seen: set[str] = set()

    for specialist in (specialist_profile or {}).get("specialists", []):
        specialist_id = specialist.get("id")
        if not specialist_id or specialist_id in seen:
            continue
        members.append(
            {
                "id": specialist_id,
                "label": specialist.get("label") or specialist_id.replace("_", " ").title(),
                "role": "advisor",
                "source": specialist.get("source") or (specialist_profile or {}).get("selection_source") or "auto",
                "purpose": specialist.get("purpose") or "",
                "domain": specialist.get("domain") or (specialist_profile or {}).get("domain"),
            }
        )
        seen.add(specialist_id)

    if members:
        members[0]["role"] = "lead"
        return members[:6]

    for specialist_id in normalize_requested_specialists(requested_specialists):
        definition = SPECIALIST_DEFINITIONS.get(specialist_id)
        if not definition or specialist_id in seen:
            continue
        members.append(
            {
                "id": specialist_id,
                "label": definition["label"],
                "role": "advisor",
                "source": "manual",
                "purpose": definition["purpose"],
                "domain": "manual",
            }
        )
        seen.add(specialist_id)

    if members:
        members[0]["role"] = "lead"
        return members[:6]

    mode_profile = MODE_STRATEGIES[response_mode]
    return [
        {
            "id": f"{response_mode}_fallback",
            "label": mode_profile["fallback_label"],
            "role": "lead",
            "source": "mode_core",
            "purpose": mode_profile["fallback_purpose"],
            "domain": "core",
        }
    ]


def _build_execution_path(
    response_mode: str,
    memory_count: int,
    workspace_hits: int,
    research_sources: int,
    policy_status: dict | None,
    tool_label: str | None = None,
) -> list[dict]:
    path: list[dict] = []
    if memory_count:
        path.append({"id": "memory", "label": "Memory"})
    if workspace_hits:
        path.append({"id": "workspace", "label": "Workspace"})
    if research_sources:
        path.append({"id": "research", "label": "Research"})
    if response_mode in {"think", "debug", "builder", "research", "operator"}:
        path.append({"id": "plan", "label": "Plan"})
    if (policy_status or {}).get("posture") not in {None, "", "nominal"}:
        path.append({"id": "policy", "label": "Policy"})
    if tool_label:
        path.append({"id": "tool", "label": "Tool"})
    if not path:
        path.append({"id": "dialogue", "label": "Dialogue"})
    return path


def _select_action_bias(
    response_mode: str,
    workspace_hits: int,
    research_sources: int,
    policy_status: dict | None,
    tool_type: str | None = None,
) -> str:
    posture = (policy_status or {}).get("posture", "nominal")
    if tool_type == "action_request":
        return "await_operator_approval"
    if tool_type == "action_result":
        return "verify_after_action"
    if tool_type:
        return "tool_first_resolution"
    if response_mode == "tiny":
        return "answer_directly"
    if posture in {"degraded", "cautious"}:
        return "guard_and_verify"
    if response_mode == "fast":
        return "answer_directly"
    if response_mode == "think":
        return "synthesize_current_evidence" if research_sources else "deliberate_then_answer"
    if response_mode == "debug":
        return "inspect_local_artifacts" if workspace_hits else "isolate_then_verify"
    if response_mode == "builder":
        return "sequence_smallest_working_slice"
    if response_mode == "research":
        return "synthesize_current_evidence"
    if response_mode == "operator":
        return "verify_then_act"
    return "answer_directly"


def _build_arbiter_rule(
    response_mode: str,
    workspace_hits: int,
    research_sources: int,
    policy_status: dict | None,
    selection_source: str | None,
    tool_type: str | None = None,
) -> str:
    posture = (policy_status or {}).get("posture", "nominal")
    if tool_type == "action_request":
        return "Do not execute blindly. Hold on the approval boundary and state the safest next confirmation step."
    if tool_type == "action_result":
        return "Assume the action ran. Focus on what changed and what to verify next."
    if posture == "degraded":
        return "Favor the safest locally verifiable path and avoid speculative leaps."
    if response_mode == "tiny":
        return "Prefer gentle clarity, one insight at a time, and no system or operator framing."
    if response_mode == "research" or research_sources:
        return "Prefer current sourced evidence, then local workspace evidence, then memory."
    if response_mode == "debug":
        return "Prefer concrete failure signals, then the smallest proof step, over broad advice."
    if response_mode == "builder":
        return "Prefer the smallest shippable slice that preserves local stability."
    if response_mode == "operator":
        return "Prefer verified local state, safe actions, and explicit approvals over speed."
    if selection_source in {"manual", "hybrid"} and workspace_hits:
        return "Honor the pinned specialists, but break ties with the strongest local evidence."
    return "Lead with the clearest grounded answer and suppress hidden internal deliberation."


def build_god_brain_trace(
    *,
    user_message: str,
    response_mode: str,
    current_goal: str | None = None,
    contract: str | None = None,
    specialist_profile: dict | None = None,
    specialist_preset: dict | None = None,
    requested_specialists=None,
    memory_count: int = 0,
    workspace_hits: int = 0,
    research_sources: int = 0,
    policy_status: dict | None = None,
    mode_guidance: dict | None = None,
    tool_type: str | None = None,
    tool_label: str | None = None,
    active_cognitive_runtimes=None,
    nova_face: dict | None = None,
    jarvis_core_binding: dict | None = None,
) -> dict:
    """Build a compact orchestration trace for the current turn."""
    normalized_mode = _normalize_response_mode(response_mode)
    mode_profile = MODE_STRATEGIES[normalized_mode]
    surface_identity = str(
        (mode_guidance or {}).get("surface_identity")
        or (mode_guidance or {}).get("resolved_voice")
        or ("tiny_nova" if normalized_mode == "tiny" else "jarvis")
    ).strip() or ("tiny_nova" if normalized_mode == "tiny" else "jarvis")
    authority_summary = (
        "Tiny Nova may front the companion surface, but Jarvis remains the authority core."
        if surface_identity == "tiny_nova"
        else "Jarvis remains the authority core for this turn."
    )
    selection_source = (specialist_profile or {}).get("selection_source")
    if specialist_preset and selection_source not in {"manual", "hybrid"}:
        selection_source = "preset"
    council = [_build_arbiter_member(normalized_mode, current_goal)]
    council.extend(
        _build_specialist_members(
            normalized_mode,
            specialist_profile=specialist_profile,
            requested_specialists=requested_specialists,
        )
    )
    lead = next((member for member in council if member.get("role") == "lead"), council[0])
    manual_specialist_count = len(
        [member for member in council if member.get("source") == "manual"]
    )
    auto_specialist_count = len(
        [member for member in council if member.get("source") in {"auto", "hybrid"}]
    )

    confidence = 0.42
    confidence += min(memory_count, 4) * 0.03
    confidence += min(workspace_hits, 4) * 0.06
    confidence += min(research_sources, 4) * 0.05
    confidence += min(len(council) - 1, 4) * 0.04
    if selection_source in {"manual", "hybrid"}:
        confidence += 0.05
    if tool_type:
        confidence += 0.08
    if (policy_status or {}).get("posture") == "cautious":
        confidence -= 0.04
    elif (policy_status or {}).get("posture") == "degraded":
        confidence -= 0.12
    if (mode_guidance or {}).get("auto_applied"):
        confidence += 0.03
    confidence = round(_clamp(confidence, 0.22, 0.96), 2)

    disagreement = 0.18
    if not specialist_profile and not requested_specialists:
        disagreement += 0.08
    if selection_source == "hybrid":
        disagreement += 0.18
    elif selection_source == "manual":
        disagreement += 0.06
    elif selection_source == "preset":
        disagreement += 0.04
    if (specialist_profile or {}).get("domain") == "mixed":
        disagreement += 0.1
    if research_sources and workspace_hits:
        disagreement += 0.05
    if (policy_status or {}).get("posture") == "degraded":
        disagreement += 0.08
    disagreement = round(_clamp(disagreement, 0.08, 0.92), 2)

    action_bias = _select_action_bias(
        normalized_mode,
        workspace_hits=workspace_hits,
        research_sources=research_sources,
        policy_status=policy_status,
        tool_type=tool_type,
    )
    action_bias_label = ACTION_BIAS_LABELS[action_bias]
    execution_path = _build_execution_path(
        normalized_mode,
        memory_count=memory_count,
        workspace_hits=workspace_hits,
        research_sources=research_sources,
        policy_status=policy_status,
        tool_label=tool_label,
    )
    arbitration_rule = _build_arbiter_rule(
        normalized_mode,
        workspace_hits=workspace_hits,
        research_sources=research_sources,
        policy_status=policy_status,
        selection_source=selection_source,
        tool_type=tool_type,
    )

    strategy_id = mode_profile["strategy_id"] if not tool_type else "tool_first_resolution"
    strategy_label = mode_profile["strategy_label"] if not tool_type else "Tool-First Resolution"
    strategy_summary = mode_profile["summary"]
    if tool_type == "action_request":
        strategy_summary = "The God Brain chose an approval-first operator path instead of a second model pass."
    elif tool_type == "action_result":
        strategy_summary = "The God Brain treated the completed tool action as the primary turn outcome."
    elif tool_type:
        strategy_summary = "The God Brain resolved the turn through a direct tool path first."

    council_labels = ", ".join(member["label"] for member in council[:5])
    summary = (
        f"God Brain chose {strategy_label}, led by {lead['label']}, with "
        f"{_disagreement_label(disagreement)} across {len(council)} minds."
    )
    instruction = (
        f"God Brain strategy: {strategy_label}. "
        f"Lead with {lead['label']} and let Sovereign Core arbitrate silently. "
        f"Action bias: {action_bias_label}. "
        f"Arbitration rule: {arbitration_rule} "
        "Use the council silently and return one clean final answer without mentioning hidden deliberation."
    )

    return {
        "strategy_id": strategy_id,
        "strategy_label": strategy_label,
        "strategy_summary": strategy_summary,
        "summary": summary,
        "current_goal": _clip(current_goal or "make forward progress", 140),
        "message_preview": _clip(user_message, 160),
        "contract": contract or "direct_answer",
        "authority_lane": "jarvis",
        "routing_authority": "jarvis",
        "surface_identity": surface_identity,
        "surface_priority": "delegated_surface" if surface_identity != "jarvis" else "authority_surface",
        "surface_replaces_authority": False,
        "authority_model": "layered_role_specialized",
        "system_shape": "organismic",
        "authority_summary": authority_summary,
        "lead": lead,
        "council": council[:7],
        "council_size": len(council),
        "council_summary": council_labels,
        "manual_specialist_count": manual_specialist_count,
        "auto_specialist_count": auto_specialist_count,
        "selection_source": selection_source or ("manual" if manual_specialist_count else "mode_core"),
        "specialist_preset": specialist_preset,
        "action_bias": action_bias,
        "action_bias_label": action_bias_label,
        "execution_path": execution_path,
        "arbiter": {
            "label": "Sovereign Core",
            "rule": arbitration_rule,
            "confidence": confidence,
            "confidence_label": _confidence_label(confidence),
            "disagreement": disagreement,
            "disagreement_label": _disagreement_label(disagreement),
        },
        "instruction": instruction,
        "active_cognitive_runtimes": list(active_cognitive_runtimes or []),
        "nova_face": dict(nova_face or {}),
        "jarvis_core_binding": dict(jarvis_core_binding or {}),
    }
