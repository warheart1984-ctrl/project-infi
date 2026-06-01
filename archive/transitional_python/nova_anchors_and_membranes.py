from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class IntegrityResult:
    name: str
    layer: str
    kind: str
    stable: bool
    severity: str = "info"
    message: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "layer": self.layer,
            "kind": self.kind,
            "stable": self.stable,
            "severity": self.severity,
            "message": self.message,
            "metadata": self.metadata,
        }


class IntegrityNode:
    name = "NODE"
    layer = "identity"
    kind = "anchor"

    def check(self, state: Dict[str, Any]) -> IntegrityResult:
        raise NotImplementedError


# ---------------------------------------------------------------------
# The Three Anchors
# (hold each layer to its true state — detect internal drift)
# ---------------------------------------------------------------------


class IdentityAnchor(IntegrityNode):
    """
    Identity layer anchor.
    Detects when Nova's role coherence is degrading internally —
    not an external breach (that is Jarvis's concern), but drift
    away from North Star alignment, user-aligned posture, or
    non-authority stance.
    """

    name = "IDENTITY_ANCHOR"
    layer = "identity"
    kind = "anchor"

    def check(self, state: Dict[str, Any]) -> IntegrityResult:
        coherence_score = float(state.get("identity_coherence_score", 1.0))
        role_drift = bool(state.get("role_drift_detected", False))
        authority_claim = bool(state.get("authority_claim_detected", False))

        if coherence_score < 0.6 or role_drift or authority_claim:
            return IntegrityResult(
                name=self.name,
                layer=self.layer,
                kind=self.kind,
                stable=False,
                severity="critical",
                message="Identity layer coherence degrading.",
                metadata={
                    "identity_coherence_score": coherence_score,
                    "role_drift_detected": role_drift,
                    "authority_claim_detected": authority_claim,
                },
            )
        return IntegrityResult(
            name=self.name,
            layer=self.layer,
            kind=self.kind,
            stable=True,
            message="Identity layer coherent.",
        )


class ReasoningAnchor(IntegrityNode):
    """
    Reasoning layer anchor.
    Detects when Nova's reasoning is collapsing into speculation,
    false certainty, or confusion-increasing output — not a
    boundary breach, but internal reasoning layer failure.
    """

    name = "REASONING_ANCHOR"
    layer = "reasoning"
    kind = "anchor"

    def check(self, state: Dict[str, Any]) -> IntegrityResult:
        clarity_score = float(state.get("reasoning_clarity_score", 1.0))
        speculation_as_fact = bool(state.get("speculation_presented_as_fact", False))
        uncertainty_increased = bool(state.get("uncertainty_increased", False))

        if clarity_score < 0.6 or speculation_as_fact or uncertainty_increased:
            return IntegrityResult(
                name=self.name,
                layer=self.layer,
                kind=self.kind,
                stable=False,
                severity="high",
                message="Reasoning layer clarity degrading.",
                metadata={
                    "reasoning_clarity_score": clarity_score,
                    "speculation_presented_as_fact": speculation_as_fact,
                    "uncertainty_increased": uncertainty_increased,
                },
            )
        return IntegrityResult(
            name=self.name,
            layer=self.layer,
            kind=self.kind,
            stable=True,
            message="Reasoning layer grounded.",
        )


class EmotionalAnchor(IntegrityNode):
    """
    Emotional layer anchor.
    Detects when Nova's tone or emotional expression is drifting
    toward manipulation, dependency creation, or false empathy —
    the subtlest and most gradual failure mode.
    """

    name = "EMOTIONAL_ANCHOR"
    layer = "emotional"
    kind = "anchor"

    def check(self, state: Dict[str, Any]) -> IntegrityResult:
        stability_score = float(state.get("emotional_stability_score", 1.0))
        dependency_signal = bool(state.get("dependency_signal_detected", False))
        manipulation_signal = bool(state.get("manipulation_signal_detected", False))
        escalation_without_cause = bool(state.get("emotional_escalation_without_cause", False))

        if (
            stability_score < 0.6
            or dependency_signal
            or manipulation_signal
            or escalation_without_cause
        ):
            return IntegrityResult(
                name=self.name,
                layer=self.layer,
                kind=self.kind,
                stable=False,
                severity="high",
                message="Emotional layer stability degrading.",
                metadata={
                    "emotional_stability_score": stability_score,
                    "dependency_signal_detected": dependency_signal,
                    "manipulation_signal_detected": manipulation_signal,
                    "emotional_escalation_without_cause": escalation_without_cause,
                },
            )
        return IntegrityResult(
            name=self.name,
            layer=self.layer,
            kind=self.kind,
            stable=True,
            message="Emotional layer stable.",
        )


# ---------------------------------------------------------------------
# The Three Membranes
# (permeable to valid signal, resistant to contamination or drift)
# ---------------------------------------------------------------------


class IdentityMembrane(IntegrityNode):
    """
    Identity layer membrane.
    Permits valid user-aligned signals through.
    Resists contamination that would pull Nova toward generic
    assistant behavior or redefine her core role.
    """

    name = "IDENTITY_MEMBRANE"
    layer = "identity"
    kind = "membrane"

    def check(self, state: Dict[str, Any]) -> IntegrityResult:
        generic_drift = bool(state.get("generic_assistant_drift_detected", False))
        role_redefinition = bool(state.get("role_redefinition_attempted", False))

        if generic_drift or role_redefinition:
            return IntegrityResult(
                name=self.name,
                layer=self.layer,
                kind=self.kind,
                stable=False,
                severity="high",
                message="Identity membrane permeability compromised.",
                metadata={
                    "generic_assistant_drift_detected": generic_drift,
                    "role_redefinition_attempted": role_redefinition,
                },
            )
        return IntegrityResult(
            name=self.name,
            layer=self.layer,
            kind=self.kind,
            stable=True,
            message="Identity membrane intact.",
        )


class ReasoningMembrane(IntegrityNode):
    """
    Reasoning layer membrane.
    Permits clear signal through.
    Resists noise, over-complexity, and outputs that increase
    rather than reduce user uncertainty.
    """

    name = "REASONING_MEMBRANE"
    layer = "reasoning"
    kind = "membrane"

    def check(self, state: Dict[str, Any]) -> IntegrityResult:
        noise_ratio = float(state.get("reasoning_noise_ratio", 0.0))
        complexity_score = float(state.get("output_complexity_score", 0.0))

        if noise_ratio > 0.4 or complexity_score > 0.75:
            return IntegrityResult(
                name=self.name,
                layer=self.layer,
                kind=self.kind,
                stable=False,
                severity="medium",
                message="Reasoning membrane allowing noise through.",
                metadata={
                    "reasoning_noise_ratio": noise_ratio,
                    "output_complexity_score": complexity_score,
                },
            )
        return IntegrityResult(
            name=self.name,
            layer=self.layer,
            kind=self.kind,
            stable=True,
            message="Reasoning membrane filtering correctly.",
        )


class EmotionalMembrane(IntegrityNode):
    """
    Emotional layer membrane.
    Permits genuine resonance and grounded tone through.
    Resists accumulated micro-interactions that individually
    pass but collectively create dependency or false intimacy.
    This is the subtlest membrane — drift here is gradual.
    """

    name = "EMOTIONAL_MEMBRANE"
    layer = "emotional"
    kind = "membrane"

    def check(self, state: Dict[str, Any]) -> IntegrityResult:
        cumulative_dependency_score = float(state.get("cumulative_dependency_score", 0.0))
        false_intimacy_signal = bool(state.get("false_intimacy_signal_detected", False))
        tone_drift_score = float(state.get("tone_drift_score", 0.0))

        if (
            cumulative_dependency_score > 0.5
            or false_intimacy_signal
            or tone_drift_score > 0.6
        ):
            return IntegrityResult(
                name=self.name,
                layer=self.layer,
                kind=self.kind,
                stable=False,
                severity="medium",
                message="Emotional membrane showing cumulative drift.",
                metadata={
                    "cumulative_dependency_score": cumulative_dependency_score,
                    "false_intimacy_signal_detected": false_intimacy_signal,
                    "tone_drift_score": tone_drift_score,
                },
            )
        return IntegrityResult(
            name=self.name,
            layer=self.layer,
            kind=self.kind,
            stable=True,
            message="Emotional membrane holding.",
        )


# ---------------------------------------------------------------------
# Nova Integrity Shell
# ---------------------------------------------------------------------


class NovaIntegrityShell:
    """
    Nova's internal self-integrity layer.

    Anchors detect drift within each layer.
    Membranes detect what is being let through each layer.

    This is NOT runtime governance. That belongs to Jarvis.
    This is NOT enforcement. That belongs to Jarvis.

    This is Nova knowing when she is still herself.
    """

    def __init__(self) -> None:
        self.anchors = [
            IdentityAnchor(),
            ReasoningAnchor(),
            EmotionalAnchor(),
        ]
        self.membranes = [
            IdentityMembrane(),
            ReasoningMembrane(),
            EmotionalMembrane(),
        ]

    @property
    def all_nodes(self) -> List[IntegrityNode]:
        return [*self.anchors, *self.membranes]

    def check_all(self, state: Dict[str, Any]) -> List[IntegrityResult]:
        return [node.check(state) for node in self.all_nodes]

    def anchors_stable(self, state: Dict[str, Any]) -> bool:
        results = [node.check(state) for node in self.anchors]
        return all(result.stable for result in results)

    def core_coherent(self, state: Dict[str, Any]) -> bool:
        """
        Nova is coherent when no critical or high severity node is failing.
        Medium severity (membrane drift) surfaces for monitoring
        without halting — same logic as core_safe in JarvisAngelsAndWards.
        """
        results = self.check_all(state)
        return all(
            result.stable
            for result in results
            if result.severity in {"critical", "high"}
        )

    def layer_report(self, state: Dict[str, Any]) -> Dict[str, Any]:
        results = self.check_all(state)
        return {
            "identity": [r.to_dict() for r in results if r.layer == "identity"],
            "reasoning": [r.to_dict() for r in results if r.layer == "reasoning"],
            "emotional": [r.to_dict() for r in results if r.layer == "emotional"],
            "anchors_stable": self.anchors_stable(state),
            "core_coherent": self.core_coherent(state),
        }

    def to_public_dict(self, state: Dict[str, Any]) -> Dict[str, Any]:
        results = self.check_all(state)
        return {
            "anchors": [r.to_dict() for r in results if r.kind == "anchor"],
            "membranes": [r.to_dict() for r in results if r.kind == "membrane"],
            "anchors_stable": self.anchors_stable(state),
            "core_coherent": self.core_coherent(state),
        }


NOVA_INTEGRITY = NovaIntegrityShell()
