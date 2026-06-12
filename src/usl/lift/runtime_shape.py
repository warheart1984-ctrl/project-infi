"""Default runtime shape until loop/blocking heuristics exist."""

from __future__ import annotations

from src.usl.lift.types import AAISHealthProfile, AAISRuntimeProfile


def lift_runtime_shape_default() -> AAISRuntimeProfile:
    return AAISRuntimeProfile(
        process_model="oneshot",
        admission="single",
        health=AAISHealthProfile(probe="lift-default", interval_seconds=30),
    )
