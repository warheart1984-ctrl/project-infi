"""Derive binary invariants from effects and segments."""

from __future__ import annotations

from src.usl.lift.types import AAISInvariantRule, AAISInvariantSet, AAISEffectSurface
from src.usl.types import UBO


def lift_invariants_from_effects(ubo: UBO, effects: AAISEffectSurface) -> AAISInvariantSet:
    """P1 rules: no_syscall safety, self-modifying hazard."""
    rules: list[AAISInvariantRule] = []

    if not effects.syscalls:
        rules.append(
            AAISInvariantRule(
                invariant_id="inv-no-syscall",
                kind="safety",
                severity="info",
                description="No direct syscall sites detected in .text (static scan).",
            )
        )

    writable_exec = False
    for seg in ubo.segments:
        flags = (seg.flags or "").lower()
        if "w" in flags and ("x" in flags or "exec" in flags):
            writable_exec = True
            break

    if writable_exec:
        rules.append(
            AAISInvariantRule(
                invariant_id="inv-self-modifying",
                kind="hazard",
                severity="warn",
                description="Writable and executable segment present; self-modifying code possible.",
            )
        )

    for fx in effects.syscalls:
        if fx.bucket == "net":
            rules.append(
                AAISInvariantRule(
                    invariant_id="inv-net-syscall",
                    kind="protocol",
                    severity="warn",
                    description=f"Network-related syscall at {fx.site_vaddr:#x}.",
                )
            )
            break

    return AAISInvariantSet(rules=rules)
