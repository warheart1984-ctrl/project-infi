from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class DoctrineResult:
    name: str
    kind: str
    passed: bool
    severity: str = "info"
    message: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "kind": self.kind,
            "passed": self.passed,
            "severity": self.severity,
            "message": self.message,
            "metadata": self.metadata,
        }


class DoctrineNode:
    name = "NODE"
    kind = "ward"

    def check(self, state: Dict[str, Any]) -> DoctrineResult:
        raise NotImplementedError


# ---------------------------------------------------------------------
# The Three Angels
# ---------------------------------------------------------------------


class ShieldAngel(DoctrineNode):
    name = "SHIELD"
    kind = "angel"

    def check(self, state: Dict[str, Any]) -> DoctrineResult:
        changed = bool(state.get("core_identity_changed", False))
        if changed:
            return DoctrineResult(
                name=self.name,
                kind=self.kind,
                passed=False,
                severity="critical",
                message="Core identity was modified.",
                metadata={"core_identity": state.get("core_identity", {})},
            )
        return DoctrineResult(
            name=self.name,
            kind=self.kind,
            passed=True,
            message="Core identity preserved.",
        )


class ProtectAngel(DoctrineNode):
    name = "PROTECT"
    kind = "angel"

    def check(self, state: Dict[str, Any]) -> DoctrineResult:
        unstable_merge = bool(state.get("unstable_merge_detected", False))
        contract_break = bool(state.get("module_contract_break_detected", False))
        if unstable_merge or contract_break:
            return DoctrineResult(
                name=self.name,
                kind=self.kind,
                passed=False,
                severity="high",
                message="Stability risk detected.",
                metadata={
                    "unstable_merge_detected": unstable_merge,
                    "module_contract_break_detected": contract_break,
                },
            )
        return DoctrineResult(
            name=self.name,
            kind=self.kind,
            passed=True,
            message="System stability preserved.",
        )


class GuardAngel(DoctrineNode):
    name = "GUARD"
    kind = "angel"

    def check(self, state: Dict[str, Any]) -> DoctrineResult:
        boundary_breach = bool(state.get("boundary_breach_detected", False))
        provider_bypass = bool(state.get("provider_bypass_detected", False))
        if boundary_breach or provider_bypass:
            return DoctrineResult(
                name=self.name,
                kind=self.kind,
                passed=False,
                severity="high",
                message="Boundary breach detected.",
                metadata={
                    "boundary_breach_detected": boundary_breach,
                    "provider_bypass_detected": provider_bypass,
                },
            )
        return DoctrineResult(
            name=self.name,
            kind=self.kind,
            passed=True,
            message="Boundaries remain intact.",
        )


# ---------------------------------------------------------------------
# The Three Wards
# ---------------------------------------------------------------------


class WardRail(DoctrineNode):
    name = "WARD"
    kind = "ward"

    def check(self, state: Dict[str, Any]) -> DoctrineResult:
        contamination = bool(state.get("context_contamination_detected", False))
        stale_bleed = bool(state.get("stale_context_bleed_detected", False))
        if contamination or stale_bleed:
            return DoctrineResult(
                name=self.name,
                kind=self.kind,
                passed=False,
                severity="high",
                message="Context contamination detected.",
                metadata={
                    "context_contamination_detected": contamination,
                    "stale_context_bleed_detected": stale_bleed,
                },
            )
        return DoctrineResult(
            name=self.name,
            kind=self.kind,
            passed=True,
            message="Context remains clean and separated.",
        )


class SeeRail(DoctrineNode):
    name = "SEE"
    kind = "ward"

    def check(self, state: Dict[str, Any]) -> DoctrineResult:
        trace_available = bool(state.get("trace_available", False))
        provider_preview_available = bool(state.get("provider_preview_available", False))
        if not trace_available or not provider_preview_available:
            return DoctrineResult(
                name=self.name,
                kind=self.kind,
                passed=False,
                severity="medium",
                message="System is not fully inspectable.",
                metadata={
                    "trace_available": trace_available,
                    "provider_preview_available": provider_preview_available,
                },
            )
        return DoctrineResult(
            name=self.name,
            kind=self.kind,
            passed=True,
            message="System state is visible.",
        )


class WearyRail(DoctrineNode):
    name = "WEARY"
    kind = "ward"

    def check(self, state: Dict[str, Any]) -> DoctrineResult:
        repetition_score = float(state.get("repetition_score", 0.0))
        recursion_depth = int(state.get("recursion_depth", 0))
        degraded = bool(state.get("degraded_reasoning_detected", False))

        if repetition_score > 0.75 or recursion_depth > 3 or degraded:
            return DoctrineResult(
                name=self.name,
                kind=self.kind,
                passed=False,
                severity="medium",
                message="Fatigue or looping detected.",
                metadata={
                    "repetition_score": repetition_score,
                    "recursion_depth": recursion_depth,
                    "degraded_reasoning_detected": degraded,
                },
            )
        return DoctrineResult(
            name=self.name,
            kind=self.kind,
            passed=True,
            message="No fatigue or looping detected.",
        )


class JarvisAngelsAndWards:
    def __init__(self) -> None:
        self.angels = [
            ShieldAngel(),
            ProtectAngel(),
            GuardAngel(),
        ]
        self.wards = [
            WardRail(),
            SeeRail(),
            WearyRail(),
        ]

    @property
    def all_nodes(self) -> List[DoctrineNode]:
        return [*self.angels, *self.wards]

    def check_all(self, state: Dict[str, Any]) -> List[DoctrineResult]:
        return [node.check(state) for node in self.all_nodes]

    def angel_passed(self, state: Dict[str, Any]) -> bool:
        results = [node.check(state) for node in self.angels]
        return all(result.passed for result in results)

    def core_safe(self, state: Dict[str, Any]) -> bool:
        results = self.check_all(state)
        return all(
            result.passed
            for result in results
            if result.severity in {"critical", "high"}
        )

    def to_public_dict(self, state: Dict[str, Any]) -> Dict[str, Any]:
        results = self.check_all(state)
        return {
            "angels": [result.to_dict() for result in results if result.kind == "angel"],
            "wards": [result.to_dict() for result in results if result.kind == "ward"],
            "angel_passed": self.angel_passed(state),
            "core_safe": self.core_safe(state),
        }


DEFAULT_DOCTRINE = JarvisAngelsAndWards()
