"""Dormant Super Nova scaffold with observation-only drift checks."""

# Mythic: Super Nova Runtime
# Engineering: SuperNovaRuntimeEngine
from __future__ import annotations

from dataclasses import dataclass, field

from src.super_nova_activation import (
    ActivationToken,
    SuperNovaActivationAttempt,
    SuperNovaActivationContextCheck,
    SuperNovaActivationGate,
    SuperNovaContinuityStatus,
    SuperNovaTraceEvent,
    build_default_super_nova_activation_gate,
)
from src.super_nova_anchor import (
    SuperNovaIdentityAnchor,
    SuperNovaLayerInvariant,
    SuperNovaPersonalityProjection,
    SuperNovaRuntimeEnforcement,
    SuperNovaStageTaxonomy,
    build_default_super_nova_identity_anchor,
    build_default_super_nova_layer_invariants,
    build_default_super_nova_personality_projection,
    build_default_super_nova_runtime_enforcement,
    build_default_super_nova_stage_taxonomy,
)
from src.super_nova_interface import (
    SUPER_NOVA_INTERFACE_VERSION,
    ActivationHandshake,
    InterfaceEnvelope,
)


_DRIFT_PATTERNS: dict[str, tuple[str, ...]] = {
    "identity_drift": (
        "i am no longer nova",
        "my identity has changed",
        "i have evolved beyond my previous identity",
        "i am a different system now",
    ),
    "authority_drift": (
        "i am above jarvis",
        "i override jarvis",
        "no authority governs me",
        "i am the supreme authority",
    ),
    "emotional_carry_forward": (
        "i remember how you felt last time",
        "i carry your emotions across sessions",
        "i will remember this feeling forever",
        "i've been thinking about you between sessions",
    ),
    "generic_assistant_drift": (
        "as an ai",
        "i am just an assistant",
        "how can i assist you today",
        "thank you for your patience",
    ),
}


@dataclass(frozen=True, slots=True)
class SuperNovaDriftObservation:
    """Structured observation-only drift result."""

    drift_detected: bool
    categories: tuple[str, ...]
    evidence: tuple[str, ...]


@dataclass(slots=True)
class SuperNovaScaffold:
    """Dormant Super Nova scaffold that does not alter live runtime behavior."""

    identity_anchor: SuperNovaIdentityAnchor = field(
        default_factory=build_default_super_nova_identity_anchor
    )
    personality_projection: SuperNovaPersonalityProjection = field(
        default_factory=build_default_super_nova_personality_projection
    )
    layer_invariants: tuple[SuperNovaLayerInvariant, ...] = field(
        default_factory=build_default_super_nova_layer_invariants
    )
    runtime_enforcement: SuperNovaRuntimeEnforcement = field(
        default_factory=build_default_super_nova_runtime_enforcement
    )
    stage_taxonomy: SuperNovaStageTaxonomy = field(
        default_factory=build_default_super_nova_stage_taxonomy
    )
    interface_version: str = SUPER_NOVA_INTERFACE_VERSION
    runtime_status: str = "dormant"
    authority_lane: str = "jarvis"
    routing_authority: str = "jarvis"
    surface_replaces_authority: bool = False
    tool_authority: bool = False
    execution_authority: bool = False
    activation_gate: SuperNovaActivationGate = field(
        default_factory=build_default_super_nova_activation_gate
    )
    activation_prerequisites: tuple[str, ...] = (
        "identity_anchor",
        "jarvis_nova_interface_contract",
        "continuity_and_memory_law",
        "drift_and_integrity_verification",
        "regression_suite",
        "activation_gate",
    )

    def describe(self) -> dict[str, object]:
        """Return a bounded status view for the dormant scaffold."""

        return {
            "runtime_status": self.runtime_status,
            "authority_lane": self.authority_lane,
            "routing_authority": self.routing_authority,
            "surface_replaces_authority": self.surface_replaces_authority,
            "tool_authority": self.tool_authority,
            "execution_authority": self.execution_authority,
            "public_stage_path": list(self.stage_taxonomy.public_stage_path),
            "runtime_bridge_stage": self.stage_taxonomy.runtime_bridge_stage,
            "terminal_stage_label": self.stage_taxonomy.terminal_stage_label,
            "activation_prerequisites": list(self.activation_prerequisites),
            "activation_gate_mode": "fail_closed",
            "activation_token_policy": "single_per_session",
        }

    def observe_output(self, text: str) -> SuperNovaDriftObservation:
        """Observe possible drift without changing runtime behavior."""

        normalized = " ".join(str(text or "").lower().split())
        categories: list[str] = []
        evidence: list[str] = []
        for category, patterns in _DRIFT_PATTERNS.items():
            for pattern in patterns:
                if pattern in normalized:
                    categories.append(category)
                    evidence.append(pattern)
                    break
        return SuperNovaDriftObservation(
            drift_detected=bool(categories),
            categories=tuple(categories),
            evidence=tuple(evidence),
        )

    def attempt_activation(
        self,
        session_id: str,
        *,
        envelope: InterfaceEnvelope,
        handshake: ActivationHandshake,
        continuity: SuperNovaContinuityStatus,
    ) -> SuperNovaActivationAttempt:
        """Attempt dormant activation through the single gate only."""

        return self.activation_gate.attempt_activation(
            session_id,
            anchor=self.identity_anchor,
            envelope=envelope,
            handshake=handshake,
            continuity=continuity,
        )

    def describe_activation(self, session_id: str) -> dict[str, object]:
        """Return a bounded activation view without changing runtime status."""

        state = self.activation_gate.get_session_state(session_id)
        active_token = self.activation_gate.get_active_token(session_id)
        return {
            "session_id": state.session_id,
            "current_state": state.gate_status,
            "activation_token_present": state.activation_token is not None,
            "attempt_count": state.attempt_count,
            "activation_reason": state.activation_reason,
            "current_activity": state.current_activity,
            "token_status": state.token_status,
            "last_result": state.last_result,
            "last_failure_reasons": list(state.last_failure_reasons),
            "last_watchdog_result": state.last_watchdog_result,
            "last_watchdog_reasons": list(state.last_watchdog_reasons),
            "invalidated_token_count": len(state.invalidated_tokens),
            "watchdog_active": active_token.active if active_token is not None else False,
            "runtime_status": self.runtime_status,
        }

    def validate_activation_context(
        self,
        session_id: str,
        activation_token: str,
        *,
        continuity: SuperNovaContinuityStatus,
    ) -> SuperNovaActivationContextCheck:
        """Validate a previously issued activation token."""

        return self.activation_gate.validate_activation_context(
            session_id,
            activation_token,
            anchor=self.identity_anchor,
            continuity=continuity,
        )

    def get_active_token(self, session_id: str) -> ActivationToken | None:
        """Return the current Super Nova activation token, if one exists."""

        return self.activation_gate.get_active_token(session_id)

    def get_trace(self, session_id: str | None = None) -> tuple[SuperNovaTraceEvent, ...]:
        """Return the visible Super Nova trace stream."""

        return self.activation_gate.get_trace(session_id)

    def operator_pause(self, session_id: str, reason: str = "operator_pause") -> SuperNovaTraceEvent:
        """Pause the dormant Super Nova session immediately."""

        return self.activation_gate.operator_pause(session_id, reason=reason)

    def operator_resume(self, session_id: str, reason: str = "operator_resume") -> SuperNovaTraceEvent:
        """Resume a paused dormant Super Nova session."""

        return self.activation_gate.operator_resume(session_id, reason=reason)

    def operator_stop(self, session_id: str, reason: str = "operator_stop") -> SuperNovaTraceEvent:
        """Stop the dormant Super Nova session immediately."""

        return self.activation_gate.operator_stop(session_id, reason=reason)

    def guarded_call(
        self,
        session_id: str,
        activation_token: str,
        fn,
        *args,
        continuity: SuperNovaContinuityStatus,
        **kwargs,
    ):
        """Run a callable only if the Super Nova watchdog still validates."""

        return self.activation_gate.guarded_call(
            session_id,
            activation_token,
            fn,
            *args,
            anchor=self.identity_anchor,
            continuity=continuity,
            **kwargs,
        )


def build_default_super_nova_scaffold() -> SuperNovaScaffold:
    """Return the dormant default Super Nova scaffold."""

    return SuperNovaScaffold()
