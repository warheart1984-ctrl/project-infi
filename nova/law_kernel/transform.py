from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from typing import Any

from nova.law_kernel.capability_ladders import next_capability
from nova.law_kernel.evolution_curves import capability_delta
from nova.law_kernel.models import Intent, LawContext
from nova.ucc.pit import enrich_pit2_ucc, enrich_pit3_ucc, ucc_enabled


@dataclass
class PITTransformResult:
    transformed_intent: Intent
    reasons: list[str]


def _base_upgrade(intent: Intent, context: LawContext) -> dict[str, Any]:
    payload = dict(intent.payload)

    domain = context.domain
    old_cap = int(payload.get("capability_level", 1))

    evidence_fitness = float(payload.get("pit_evidence_fitness", 0.0))
    correctness = float(payload.get("correctness_score", 0.0))

    delta = capability_delta(evidence_fitness, correctness)
    new_cap = next_capability(domain, old_cap, delta)

    payload["capability_level"] = new_cap
    payload["guardrails"] = {
        **payload.get("guardrails", {}),
        "must_preserve_reference_integrity": True,
        "must_emit_lineage": True,
        "must_bind_t5": True,
        "must_fail_closed": True,
    }

    payload["learning_bias"] = "reinforce" if correctness > 0.8 else "neutral"

    return payload


def _reflection_log_id(prefix: str, intent: Intent, context: LawContext) -> str:
    seed = f"{prefix}:{intent.id}:{context.epoch}:{context.domain}"
    return f"{prefix}-{sha256(seed.encode('utf-8')).hexdigest()[:12]}"


def pit1_transform(intent: Intent, context: LawContext) -> PITTransformResult:
    payload = _base_upgrade(intent, context)

    transformed = Intent(
        id=intent.id + ":pit1",
        kind=intent.kind,
        payload=payload,
        origin=intent.origin,
    )

    return PITTransformResult(
        transformed_intent=transformed,
        reasons=["PIT-1: capability upgrade + guardrails + learning bias"],
    )


def pit2_transform(intent: Intent, context: LawContext) -> PITTransformResult:
    payload = _base_upgrade(intent, context)

    reflection = dict(payload.get("self_reflection", {}))
    reflection.update(
        {
            "must_explain_reasoning": True,
            "must_log_assumptions": True,
            "must_track_uncertainty": True,
            "reasoning_log_id": _reflection_log_id("reasoning", intent, context),
            "assumptions_log_id": _reflection_log_id("assumptions", intent, context),
            "uncertainty_profile_id": _reflection_log_id("uncertainty", intent, context),
        }
    )
    payload["self_reflection"] = reflection
    payload["cortex_pipeline"] = ["self_reflection", "attention"]
    if ucc_enabled(intent):
        enrich_pit2_ucc(payload, intent, context)

    transformed = Intent(
        id=intent.id + ":pit2",
        kind=intent.kind,
        payload=payload,
        origin=intent.origin,
    )

    return PITTransformResult(
        transformed_intent=transformed,
        reasons=["PIT-2: self-reflection enabled (reasoning, assumptions, uncertainty)"],
    )


def pit3_transform(intent: Intent, context: LawContext) -> PITTransformResult:
    payload = _base_upgrade(intent, context)

    planning = dict(payload.get("planning_profile", {}))
    planning.update(
        {
            "must_generate_plan": True,
            "max_steps": 5,
            "must_evaluate_steps": True,
            "must_emit_plan_lineage": True,
        }
    )
    payload["planning_profile"] = planning
    payload["cortex_pipeline"] = ["planning", "attention"]
    if ucc_enabled(intent):
        enrich_pit3_ucc(payload, intent, context)

    transformed = Intent(
        id=intent.id + ":pit3",
        kind=intent.kind,
        payload=payload,
        origin=intent.origin,
    )

    return PITTransformResult(
        transformed_intent=transformed,
        reasons=["PIT-3: multi-step planning enabled (plan, evaluate, lineage)"],
    )


def transform_intent(intent: Intent, context: LawContext) -> PITTransformResult:
    mode = str(intent.payload.get("pit_mode", "PIT-1")).upper()

    if mode == "PIT-2":
        return pit2_transform(intent, context)
    if mode == "PIT-3":
        return pit3_transform(intent, context)

    return pit1_transform(intent, context)
