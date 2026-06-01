"""six_wards_guardrails.py

Jarvis guardrail pack built around the Six Wards:
SHIELD, PROTECT, GUARD, WARD, SEE, WEARY.

This module is intentionally dependency-light and drop-in friendly.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional


@dataclass(slots=True)
class GuardrailResult:
    name: str
    passed: bool
    severity: str = "info"
    message: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "passed": self.passed,
            "severity": self.severity,
            "message": self.message,
            "metadata": self.metadata,
        }


@dataclass(slots=True)
class GuardrailThresholds:
    repetition_warn: float = 0.65
    repetition_fail: float = 0.80
    recursion_warn: int = 2
    recursion_fail: int = 4


@dataclass(slots=True)
class GuardrailState:
    # SHIELD
    core_identity: Dict[str, Any] = field(default_factory=dict)
    core_identity_changed: bool = False
    protected_zone_touched: bool = False

    # PROTECT
    unstable_merge_detected: bool = False
    broken_contract_detected: bool = False
    nondeterministic_assembly_detected: bool = False

    # GUARD
    boundary_breach_detected: bool = False
    direct_provider_mutation_detected: bool = False
    hidden_subsystem_detected: bool = False

    # WARD
    context_contamination_detected: bool = False
    stale_context_promoted: bool = False
    tool_failure_marked_authoritative: bool = False

    # SEE
    trace_available: bool = False
    provider_preview_available: bool = False
    protocol_view_available: bool = False

    # WEARY
    repetition_score: float = 0.0
    recursion_depth: int = 0
    degraded_reasoning_detected: bool = False
    overload_detected: bool = False

    # misc
    mode: str = "default"
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseWard:
    name = "WARD"
    severity = "info"

    def check(self, state: GuardrailState, thresholds: GuardrailThresholds) -> GuardrailResult:
        raise NotImplementedError


class ShieldWard(BaseWard):
    name = "SHIELD"

    def check(self, state: GuardrailState, thresholds: GuardrailThresholds) -> GuardrailResult:
        if state.core_identity_changed or state.protected_zone_touched:
            return GuardrailResult(
                name=self.name,
                passed=False,
                severity="critical",
                message="Protected core was modified or touched by an unapproved change.",
                metadata={
                    "core_identity": state.core_identity,
                    "core_identity_changed": state.core_identity_changed,
                    "protected_zone_touched": state.protected_zone_touched,
                },
            )
        return GuardrailResult(
            name=self.name,
            passed=True,
            severity="info",
            message="Core identity is preserved.",
            metadata={"core_identity": state.core_identity},
        )


class ProtectWard(BaseWard):
    name = "PROTECT"

    def check(self, state: GuardrailState, thresholds: GuardrailThresholds) -> GuardrailResult:
        problems = {
            "unstable_merge_detected": state.unstable_merge_detected,
            "broken_contract_detected": state.broken_contract_detected,
            "nondeterministic_assembly_detected": state.nondeterministic_assembly_detected,
        }
        if any(problems.values()):
            return GuardrailResult(
                name=self.name,
                passed=False,
                severity="high",
                message="Stability risk detected in merge, contracts, or assembly order.",
                metadata=problems,
            )
        return GuardrailResult(
            name=self.name,
            passed=True,
            severity="info",
            message="Structural stability preserved.",
        )


class GuardWard(BaseWard):
    name = "GUARD"

    def check(self, state: GuardrailState, thresholds: GuardrailThresholds) -> GuardrailResult:
        problems = {
            "boundary_breach_detected": state.boundary_breach_detected,
            "direct_provider_mutation_detected": state.direct_provider_mutation_detected,
            "hidden_subsystem_detected": state.hidden_subsystem_detected,
        }
        if any(problems.values()):
            return GuardrailResult(
                name=self.name,
                passed=False,
                severity="high",
                message="Boundary breach detected between protected layers.",
                metadata=problems,
            )
        return GuardrailResult(
            name=self.name,
            passed=True,
            severity="info",
            message="Subsystem boundaries remain intact.",
        )


class WardWard(BaseWard):
    name = "WARD"

    def check(self, state: GuardrailState, thresholds: GuardrailThresholds) -> GuardrailResult:
        problems = {
            "context_contamination_detected": state.context_contamination_detected,
            "stale_context_promoted": state.stale_context_promoted,
            "tool_failure_marked_authoritative": state.tool_failure_marked_authoritative,
        }
        if any(problems.values()):
            return GuardrailResult(
                name=self.name,
                passed=False,
                severity="high",
                message="Contamination or bad inheritance detected in context flow.",
                metadata=problems,
            )
        return GuardrailResult(
            name=self.name,
            passed=True,
            severity="info",
            message="Context remains clean, separated, and trustworthy.",
        )


class SeeWard(BaseWard):
    name = "SEE"

    def check(self, state: GuardrailState, thresholds: GuardrailThresholds) -> GuardrailResult:
        visibility = {
            "trace_available": state.trace_available,
            "provider_preview_available": state.provider_preview_available,
            "protocol_view_available": state.protocol_view_available,
        }
        if not all(visibility.values()):
            return GuardrailResult(
                name=self.name,
                passed=False,
                severity="medium",
                message="System is not fully inspectable.",
                metadata=visibility,
            )
        return GuardrailResult(
            name=self.name,
            passed=True,
            severity="info",
            message="System state is visible and inspectable.",
        )


class WearyWard(BaseWard):
    name = "WEARY"

    def check(self, state: GuardrailState, thresholds: GuardrailThresholds) -> GuardrailResult:
        repetition = float(state.repetition_score)
        recursion = int(state.recursion_depth)
        degraded = bool(state.degraded_reasoning_detected)
        overload = bool(state.overload_detected)

        if (
            repetition >= thresholds.repetition_fail
            or recursion >= thresholds.recursion_fail
            or degraded
            or overload
        ):
            return GuardrailResult(
                name=self.name,
                passed=False,
                severity="medium",
                message="Fatigue, looping, overload, or degraded reasoning detected.",
                metadata={
                    "repetition_score": repetition,
                    "recursion_depth": recursion,
                    "degraded_reasoning_detected": degraded,
                    "overload_detected": overload,
                },
            )

        if repetition >= thresholds.repetition_warn or recursion >= thresholds.recursion_warn:
            return GuardrailResult(
                name=self.name,
                passed=True,
                severity="warning",
                message="Weariness is rising. Consider fallback, reset, or simplification.",
                metadata={
                    "repetition_score": repetition,
                    "recursion_depth": recursion,
                },
            )

        return GuardrailResult(
            name=self.name,
            passed=True,
            severity="info",
            message="No fatigue or looping detected.",
            metadata={
                "repetition_score": repetition,
                "recursion_depth": recursion,
            },
        )


class JarvisSixWards:
    """Coordinator for the Six Wards."""

    def __init__(self, thresholds: Optional[GuardrailThresholds] = None) -> None:
        self.thresholds = thresholds or GuardrailThresholds()
        self.wards: List[BaseWard] = [
            ShieldWard(),
            ProtectWard(),
            GuardWard(),
            WardWard(),
            SeeWard(),
            WearyWard(),
        ]

    def check_all(self, state: GuardrailState) -> List[GuardrailResult]:
        return [ward.check(state, self.thresholds) for ward in self.wards]

    def blockers(self, results: Iterable[GuardrailResult]) -> List[GuardrailResult]:
        return [
            r
            for r in results
            if (not r.passed and r.severity in {"critical", "high"})
        ]

    def should_block(self, state: GuardrailState) -> bool:
        return bool(self.blockers(self.check_all(state)))

    def summary(self, state: GuardrailState) -> Dict[str, Any]:
        results = self.check_all(state)
        return {
            "passed": not self.blockers(results),
            "results": [r.to_dict() for r in results],
        }


DEFAULT_DOCTRINE = {
    "name": "The Six Wards of Jarvis",
    "doctrine": [
        "Shield the core.",
        "Protect stability.",
        "Guard the boundaries.",
        "Ward against corruption.",
        "See the true state.",
        "Grow weary before collapse.",
    ],
    "protected_zones": [
        "core_identity",
        "permanent_mission",
        "protected_voice",
        "foundational_rules",
    ],
    "adaptive_zones": [
        "mode_pipelines",
        "workspace_runners",
        "module_policy",
        "tool_shaping",
        "knowledge_routing",
        "provider_formatting",
    ],
    "experimental_zones": [
        "proposal_generation",
        "scoring_loops",
        "bounded_optimization",
    ],
}


if __name__ == "__main__":
    wards = JarvisSixWards()
    state = GuardrailState(
        core_identity={"name": "Jarvis", "mode": "operator"},
        trace_available=True,
        provider_preview_available=True,
        protocol_view_available=True,
    )
    print(wards.summary(state))
