from __future__ import annotations

from dataclasses import dataclass

from nova.law_kernel.models import Intent, LawContext
from nova.law_kernel.transform import pit1_transform, pit2_transform, pit3_transform


@dataclass
class DriftVector:
    capability_delta: int
    guardrail_delta: int
    reflection_delta: int
    planning_delta: int


def compute_drift_vector(original: Intent, transformed: Intent) -> DriftVector:
    original_payload = original.payload
    transformed_payload = transformed.payload

    cap_delta = int(transformed_payload.get("capability_level", 0)) - int(
        original_payload.get("capability_level", 0)
    )

    guardrail_delta = len(transformed_payload.get("guardrails", {})) - len(
        original_payload.get("guardrails", {})
    )

    reflection_delta = len(transformed_payload.get("self_reflection", {})) - len(
        original_payload.get("self_reflection", {})
    )

    planning_delta = len(transformed_payload.get("planning_profile", {})) - len(
        original_payload.get("planning_profile", {})
    )

    return DriftVector(
        capability_delta=cap_delta,
        guardrail_delta=guardrail_delta,
        reflection_delta=reflection_delta,
        planning_delta=planning_delta,
    )


def expected_drift_bounds(mode: str) -> DriftVector:
    if mode == "PIT-1":
        return DriftVector(capability_delta=3, guardrail_delta=10, reflection_delta=0, planning_delta=0)
    if mode == "PIT-2":
        return DriftVector(capability_delta=3, guardrail_delta=10, reflection_delta=10, planning_delta=0)
    if mode == "PIT-3":
        return DriftVector(capability_delta=3, guardrail_delta=10, reflection_delta=0, planning_delta=10)
    return DriftVector(0, 0, 0, 0)


def within_bounds(actual: DriftVector, expected: DriftVector) -> bool:
    return (
        0 <= actual.capability_delta <= expected.capability_delta
        and 0 <= actual.guardrail_delta <= expected.guardrail_delta
        and 0 <= actual.reflection_delta <= expected.reflection_delta
        and 0 <= actual.planning_delta <= expected.planning_delta
    )


def drift_for_mode(intent: Intent, context: LawContext, mode: str) -> DriftVector:
    if mode == "PIT-2":
        transformed = pit2_transform(intent, context).transformed_intent
    elif mode == "PIT-3":
        transformed = pit3_transform(intent, context).transformed_intent
    else:
        transformed = pit1_transform(intent, context).transformed_intent
    return compute_drift_vector(intent, transformed)
