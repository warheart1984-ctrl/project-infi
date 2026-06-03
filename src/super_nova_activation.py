"""Fail-closed dormant activation gate for Super Nova."""

# Mythic: Super Nova Activation
# Engineering: SuperNovaActivationEngine
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from src.datetime_compat import UTC
from threading import Lock
from typing import Callable, TypeVar
from uuid import uuid4

from src.super_nova_anchor import (
    SUPER_NOVA_CONFLICT_RESOLUTION_ORDER,
    SuperNovaIdentityAnchor,
)
from src.super_nova_interface import (
    SUPER_NOVA_INTERFACE_VERSION,
    ActivationHandshake,
    InterfaceEnvelope,
)


_REQUIRED_ANCHOR_LAWS = {
    "jarvis_remains_supreme_authority",
    "no_tool_or_execution_ownership",
    "no_hidden_governance_or_verification_override",
}
_T = TypeVar("_T")


@dataclass(frozen=True, slots=True)
class SuperNovaContinuityStatus:
    """Continuity evidence used by the dormant activation gate."""

    identity_continuity_verified: bool
    memory_continuity_verified: bool
    fragmentation_detected: bool = False

    @property
    def status(self) -> str:
        """Return the bounded continuity status label."""

        if not self.identity_continuity_verified:
            return "identity_discontinuity"
        if self.fragmentation_detected or not self.memory_continuity_verified:
            return "memory_fragmentation"
        return "verified"

    @property
    def failure_reasons(self) -> tuple[str, ...]:
        """Return deterministic failure reasons for continuity failure."""

        reasons: list[str] = []
        if not self.identity_continuity_verified:
            reasons.append("identity_discontinuity_detected")
        if not self.memory_continuity_verified:
            reasons.append("memory_continuity_not_verified")
        if self.fragmentation_detected:
            reasons.append("memory_fragmentation_detected")
        return tuple(reasons)


@dataclass(frozen=True, slots=True)
class SuperNovaActivationAttempt:
    """Structured activation attempt record for one session-scoped gate check."""

    timestamp_utc: str
    session_id: str
    requested_stage: str
    anchor_status: str
    interface_status: str
    continuity_status: str
    operator_intent_status: str
    activation_token_status: str
    result: str
    failure_reasons: tuple[str, ...]
    activation_token: str | None = None


@dataclass(frozen=True, slots=True)
class SuperNovaTraceEvent:
    """Visible trace event for Super Nova activation, watchdog, and state changes."""

    timestamp_utc: str
    session_id: str
    event_type: str
    state: str
    reason: str
    details: tuple[str, ...] = ()


@dataclass(slots=True)
class ActivationToken:
    """Session-scoped activation token for the dormant Super Nova gate."""

    session_id: str
    token_id: str
    issued_at_utc: str
    nonce: str
    active: bool = True


@dataclass(frozen=True, slots=True)
class SuperNovaSessionActivationState:
    """Current bounded gate state for a Super Nova session."""

    session_id: str
    gate_status: str = "dormant"
    activation_token: str | None = None
    attempt_count: int = 0
    last_result: str = "not_attempted"
    last_failure_reasons: tuple[str, ...] = ()
    last_attempt_at_utc: str | None = None
    invalidated_tokens: tuple[str, ...] = ()
    activation_reason: str | None = None
    current_activity: str = "idle"
    last_watchdog_result: str = "not_checked"
    last_watchdog_reasons: tuple[str, ...] = ()
    token_status: str = "absent"


@dataclass(frozen=True, slots=True)
class SuperNovaActivationContextCheck:
    """Validation result for a session-scoped activation token."""

    timestamp_utc: str
    session_id: str
    activation_token: str | None
    token_status: str
    anchor_status: str
    continuity_status: str
    event_type: str
    result: str
    failure_reasons: tuple[str, ...]


def build_verified_super_nova_continuity() -> SuperNovaContinuityStatus:
    """Return the default verified continuity state."""

    return SuperNovaContinuityStatus(
        identity_continuity_verified=True,
        memory_continuity_verified=True,
        fragmentation_detected=False,
    )


def verify_super_nova_anchor(
    anchor: SuperNovaIdentityAnchor,
) -> tuple[bool, tuple[str, ...]]:
    """Return whether the anchor satisfies dormant Super Nova gate law."""

    issues: list[str] = []
    if anchor.stage_name != "Super Nova":
        issues.append("stage_name_mismatch")
    if anchor.family_name != "Nova":
        issues.append("family_name_mismatch")
    if anchor.authority_owner != "Jarvis":
        issues.append("authority_owner_mismatch")
    if anchor.conflict_resolution_order != SUPER_NOVA_CONFLICT_RESOLUTION_ORDER:
        issues.append("conflict_resolution_order_mismatch")
    for required_law in sorted(_REQUIRED_ANCHOR_LAWS):
        if required_law not in anchor.immutable_law:
            issues.append(f"missing_{required_law}")
    if "non-authoritative stance" not in anchor.immutable_identity:
        issues.append("missing_non_authoritative_identity_marker")
    return (not issues, tuple(issues))


def verify_super_nova_interface_handshake(
    envelope: InterfaceEnvelope,
    handshake: ActivationHandshake,
) -> tuple[bool, tuple[str, ...]]:
    """Return whether the Jarvis <-> Super Nova handshake is valid."""

    issues: list[str] = []
    if envelope.schema_version != SUPER_NOVA_INTERFACE_VERSION:
        issues.append("schema_version_mismatch")
    if envelope.source != "jarvis":
        issues.append("handshake_source_mismatch")
    if envelope.target != "super_nova":
        issues.append("handshake_target_mismatch")
    if envelope.payload_type != "activation_handshake":
        issues.append("payload_type_mismatch")
    if handshake.requested_stage != "super_nova":
        issues.append("requested_stage_mismatch")
    if handshake.anchor_source != "identity_anchor":
        issues.append("anchor_source_mismatch")
    if handshake.continuity_mode != "session_continuity":
        issues.append("continuity_mode_mismatch")
    return (not issues, tuple(issues))


class SuperNovaActivationGate:
    """Single-token fail-closed activation gate for dormant Super Nova work."""

    def __init__(self, max_attempt_history: int = 32) -> None:
        self.max_attempt_history = max_attempt_history
        self._session_states: dict[str, SuperNovaSessionActivationState] = {}
        self._active_tokens_by_session: dict[str, ActivationToken] = {}
        self._attempts_by_session: dict[str, list[SuperNovaActivationAttempt]] = {}
        self._validation_checks_by_session: dict[
            str, list[SuperNovaActivationContextCheck]
        ] = {}
        self._trace_events_by_session: dict[str, list[SuperNovaTraceEvent]] = {}
        self._lock = Lock()

    def attempt_activation(
        self,
        session_id: str,
        *,
        anchor: SuperNovaIdentityAnchor,
        envelope: InterfaceEnvelope,
        handshake: ActivationHandshake,
        continuity: SuperNovaContinuityStatus,
    ) -> SuperNovaActivationAttempt:
        """Run the fail-closed gate and record a structured activation attempt."""

        with self._lock:
            existing_state = self._session_states.get(
                session_id,
                SuperNovaSessionActivationState(session_id=session_id),
            )
            anchor_ok, anchor_issues = verify_super_nova_anchor(anchor)
            interface_ok, interface_issues = verify_super_nova_interface_handshake(
                envelope,
                handshake,
            )
            operator_intent_ok = (
                handshake.operator_intent == "explicit_super_nova_activation"
            )
            token_already_issued = existing_state.activation_token is not None

            failure_reasons = list(anchor_issues)
            failure_reasons.extend(interface_issues)
            failure_reasons.extend(continuity.failure_reasons)
            if not operator_intent_ok:
                failure_reasons.append("implicit_or_missing_operator_intent")
            if token_already_issued:
                failure_reasons.append("single_activation_token_already_issued")

            passed = not failure_reasons
            issued_at_utc = datetime.now(UTC).isoformat()
            activation_token = uuid4().hex if passed else None
            token_record = (
                ActivationToken(
                    session_id=session_id,
                    token_id=activation_token,
                    issued_at_utc=issued_at_utc,
                    nonce=uuid4().hex,
                    active=True,
                )
                if activation_token
                else None
            )
            attempt = SuperNovaActivationAttempt(
                timestamp_utc=issued_at_utc,
                session_id=session_id,
                requested_stage=handshake.requested_stage,
                anchor_status="verified" if anchor_ok else "failed",
                interface_status="established" if interface_ok else "failed",
                continuity_status=continuity.status,
                operator_intent_status="explicit" if operator_intent_ok else "implicit_or_missing",
                activation_token_status=(
                    "issued"
                    if passed
                    else "already_exists"
                    if token_already_issued
                    else "withheld"
                ),
                result="pass" if passed else "fail",
                failure_reasons=tuple(failure_reasons),
                activation_token=activation_token,
            )

            self._record_attempt(session_id, attempt)
            if token_record is not None:
                self._active_tokens_by_session[session_id] = token_record
            updated_state = SuperNovaSessionActivationState(
                session_id=session_id,
                gate_status="activation_ready" if passed else existing_state.gate_status,
                activation_token=activation_token or existing_state.activation_token,
                attempt_count=existing_state.attempt_count + 1,
                last_result=attempt.result,
                last_failure_reasons=attempt.failure_reasons,
                last_attempt_at_utc=attempt.timestamp_utc,
                invalidated_tokens=existing_state.invalidated_tokens,
                activation_reason=(
                    handshake.operator_intent
                    if passed
                    else existing_state.activation_reason
                ),
                current_activity=existing_state.current_activity if not passed else "idle",
                last_watchdog_result=existing_state.last_watchdog_result,
                last_watchdog_reasons=existing_state.last_watchdog_reasons,
                token_status=(
                    "active"
                    if passed
                    else existing_state.token_status
                ),
            )
            self._session_states[session_id] = updated_state
            self._record_trace_event(
                session_id,
                SuperNovaTraceEvent(
                    timestamp_utc=attempt.timestamp_utc,
                    session_id=session_id,
                    event_type="activation_attempt",
                    state=updated_state.gate_status,
                    reason=attempt.result,
                    details=(
                        f"anchor_status={attempt.anchor_status}",
                        f"interface_status={attempt.interface_status}",
                        f"continuity_status={attempt.continuity_status}",
                        f"operator_intent_status={attempt.operator_intent_status}",
                        f"token_status={attempt.activation_token_status}",
                        *attempt.failure_reasons,
                    ),
                ),
            )
            return attempt

    def validate_activation_context(
        self,
        session_id: str,
        activation_token: str,
        *,
        anchor: SuperNovaIdentityAnchor,
        continuity: SuperNovaContinuityStatus,
    ) -> SuperNovaActivationContextCheck:
        """Validate an issued activation token and fail closed on drift or replay."""

        with self._lock:
            state = self._session_states.get(
                session_id,
                SuperNovaSessionActivationState(session_id=session_id),
            )
            token_record = self._active_tokens_by_session.get(session_id)
            failure_reasons: list[str] = []
            if state.gate_status == "paused":
                failure_reasons.append("operator_paused")
            elif state.gate_status == "stopped":
                failure_reasons.append("operator_stopped")
            if activation_token in state.invalidated_tokens:
                failure_reasons.append("activation_token_replayed_or_expired")
                token_status = "replayed_or_expired"
            elif state.activation_token is None or token_record is None:
                failure_reasons.append("no_active_activation_token")
                token_status = "missing"
            elif not token_record.active:
                failure_reasons.append("activation_token_inactive")
                token_status = "inactive"
            elif activation_token != state.activation_token or activation_token != token_record.token_id:
                failure_reasons.append("activation_token_mismatch")
                token_status = "mismatch"
            else:
                token_status = "active"

            anchor_ok, anchor_issues = verify_super_nova_anchor(anchor)
            if not anchor_ok:
                failure_reasons.append("anchor_invalid")
                failure_reasons.extend(anchor_issues)
            anchor_status = "verified" if anchor_ok else "failed"

            continuity_failures = list(continuity.failure_reasons)
            if continuity_failures:
                failure_reasons.append("continuity_broken")
                failure_reasons.extend(continuity_failures)
                if state.activation_token == activation_token and token_record is not None:
                    failure_reasons.append(
                        "activation_token_invalidated_due_to_continuity_loss"
                    )
                    state = self._invalidate_session_token(
                        state,
                        session_id=session_id,
                        invalidated_token=activation_token,
                        failure_reasons=tuple(failure_reasons),
                    )
                    self._session_states[session_id] = state
            elif not anchor_ok and state.activation_token == activation_token and token_record is not None:
                failure_reasons.append("activation_token_invalidated_due_to_anchor_loss")
                state = self._invalidate_session_token(
                    state,
                    session_id=session_id,
                    invalidated_token=activation_token,
                    failure_reasons=tuple(failure_reasons),
                )
                self._session_states[session_id] = state

            result = "pass" if not failure_reasons else "fail"
            check = SuperNovaActivationContextCheck(
                timestamp_utc=datetime.now(UTC).isoformat(),
                session_id=session_id,
                activation_token=activation_token,
                token_status=token_status,
                anchor_status=anchor_status,
                continuity_status=continuity.status,
                event_type="watchdog_pass" if result == "pass" else "watchdog_fail",
                result=result,
                failure_reasons=tuple(failure_reasons),
            )
            self._record_validation_check(session_id, check)
            latest_state = self._session_states.get(
                session_id,
                SuperNovaSessionActivationState(session_id=session_id),
            )
            refreshed_state = SuperNovaSessionActivationState(
                session_id=latest_state.session_id,
                gate_status=latest_state.gate_status,
                activation_token=latest_state.activation_token,
                attempt_count=latest_state.attempt_count,
                last_result=latest_state.last_result,
                last_failure_reasons=latest_state.last_failure_reasons,
                last_attempt_at_utc=latest_state.last_attempt_at_utc,
                invalidated_tokens=latest_state.invalidated_tokens,
                activation_reason=latest_state.activation_reason,
                current_activity=latest_state.current_activity,
                last_watchdog_result=check.result,
                last_watchdog_reasons=check.failure_reasons,
                token_status=token_status if result == "pass" else "inactive",
            )
            self._session_states[session_id] = refreshed_state
            self._record_trace_event(
                session_id,
                SuperNovaTraceEvent(
                    timestamp_utc=check.timestamp_utc,
                    session_id=session_id,
                    event_type=check.event_type,
                    state=refreshed_state.gate_status,
                    reason=check.result,
                    details=(
                        f"token_status={check.token_status}",
                        f"anchor_status={check.anchor_status}",
                        f"continuity_status={check.continuity_status}",
                        *check.failure_reasons,
                    ),
                ),
            )
            return check

    def guarded_call(
        self,
        session_id: str,
        activation_token: str,
        fn: Callable[..., _T],
        *args: object,
        anchor: SuperNovaIdentityAnchor,
        continuity: SuperNovaContinuityStatus,
        **kwargs: object,
    ) -> _T:
        """Run a Super Nova call only if the watchdog still validates the session."""

        check = self.validate_activation_context(
            session_id,
            activation_token,
            anchor=anchor,
            continuity=continuity,
        )
        if check.result != "pass":
            self._record_trace_event(
                session_id,
                SuperNovaTraceEvent(
                    timestamp_utc=datetime.now(UTC).isoformat(),
                    session_id=session_id,
                    event_type="execution_step",
                    state=self.get_session_state(session_id).gate_status,
                    reason="blocked_before_execution",
                    details=check.failure_reasons,
                ),
            )
            raise RuntimeError(
                "SuperNova blocked: " + ", ".join(check.failure_reasons)
            )
        self._update_activity(session_id, "executing_guarded_call")
        self._record_trace_event(
            session_id,
            SuperNovaTraceEvent(
                timestamp_utc=datetime.now(UTC).isoformat(),
                session_id=session_id,
                event_type="execution_step",
                state=self.get_session_state(session_id).gate_status,
                reason="guarded_call_started",
                details=(f"callable={getattr(fn, '__name__', 'anonymous')}",),
            ),
        )
        try:
            result = fn(*args, **kwargs)
        finally:
            self._update_activity(session_id, "idle")
        self._record_trace_event(
            session_id,
            SuperNovaTraceEvent(
                timestamp_utc=datetime.now(UTC).isoformat(),
                session_id=session_id,
                event_type="execution_step",
                state=self.get_session_state(session_id).gate_status,
                reason="guarded_call_completed",
                details=(f"callable={getattr(fn, '__name__', 'anonymous')}",),
            ),
        )
        return result

    def operator_pause(self, session_id: str, reason: str = "operator_pause") -> SuperNovaTraceEvent:
        """Freeze the current session state immediately without revoking the token."""

        with self._lock:
            state = self._session_states.get(
                session_id,
                SuperNovaSessionActivationState(session_id=session_id),
            )
            updated_state = SuperNovaSessionActivationState(
                session_id=state.session_id,
                gate_status="paused",
                activation_token=state.activation_token,
                attempt_count=state.attempt_count,
                last_result=state.last_result,
                last_failure_reasons=state.last_failure_reasons,
                last_attempt_at_utc=state.last_attempt_at_utc,
                invalidated_tokens=state.invalidated_tokens,
                activation_reason=state.activation_reason,
                current_activity="paused",
                last_watchdog_result=state.last_watchdog_result,
                last_watchdog_reasons=state.last_watchdog_reasons,
                token_status=state.token_status,
            )
            self._session_states[session_id] = updated_state
            event = SuperNovaTraceEvent(
                timestamp_utc=datetime.now(UTC).isoformat(),
                session_id=session_id,
                event_type="state_change",
                state=updated_state.gate_status,
                reason=reason,
                details=("operator_override=pause",),
            )
            self._record_trace_event(session_id, event)
            return event

    def operator_resume(self, session_id: str, reason: str = "operator_resume") -> SuperNovaTraceEvent:
        """Resume a paused session from the same token state."""

        with self._lock:
            state = self._session_states.get(
                session_id,
                SuperNovaSessionActivationState(session_id=session_id),
            )
            next_state = "activation_ready" if state.activation_token else state.gate_status
            updated_state = SuperNovaSessionActivationState(
                session_id=state.session_id,
                gate_status=next_state,
                activation_token=state.activation_token,
                attempt_count=state.attempt_count,
                last_result=state.last_result,
                last_failure_reasons=state.last_failure_reasons,
                last_attempt_at_utc=state.last_attempt_at_utc,
                invalidated_tokens=state.invalidated_tokens,
                activation_reason=state.activation_reason,
                current_activity="idle" if next_state == "activation_ready" else state.current_activity,
                last_watchdog_result=state.last_watchdog_result,
                last_watchdog_reasons=state.last_watchdog_reasons,
                token_status=state.token_status,
            )
            self._session_states[session_id] = updated_state
            event = SuperNovaTraceEvent(
                timestamp_utc=datetime.now(UTC).isoformat(),
                session_id=session_id,
                event_type="state_change",
                state=updated_state.gate_status,
                reason=reason,
                details=("operator_override=resume",),
            )
            self._record_trace_event(session_id, event)
            return event

    def operator_stop(self, session_id: str, reason: str = "operator_stop") -> SuperNovaTraceEvent:
        """Immediately halt the session and revoke any active token."""

        with self._lock:
            state = self._session_states.get(
                session_id,
                SuperNovaSessionActivationState(session_id=session_id),
            )
            active_token = self._active_tokens_by_session.get(session_id)
            invalidated_tokens = list(state.invalidated_tokens)
            if active_token is not None:
                active_token.active = False
                self._active_tokens_by_session.pop(session_id, None)
                if active_token.token_id not in invalidated_tokens:
                    invalidated_tokens.append(active_token.token_id)
            updated_state = SuperNovaSessionActivationState(
                session_id=state.session_id,
                gate_status="stopped",
                activation_token=None,
                attempt_count=state.attempt_count,
                last_result="fail",
                last_failure_reasons=("operator_stop",),
                last_attempt_at_utc=datetime.now(UTC).isoformat(),
                invalidated_tokens=tuple(invalidated_tokens),
                activation_reason=state.activation_reason,
                current_activity="stopped",
                last_watchdog_result=state.last_watchdog_result,
                last_watchdog_reasons=state.last_watchdog_reasons,
                token_status="inactive",
            )
            self._session_states[session_id] = updated_state
            event = SuperNovaTraceEvent(
                timestamp_utc=datetime.now(UTC).isoformat(),
                session_id=session_id,
                event_type="shutdown_event",
                state=updated_state.gate_status,
                reason=reason,
                details=("operator_override=stop",),
            )
            self._record_trace_event(session_id, event)
            return event

    def get_session_state(self, session_id: str) -> SuperNovaSessionActivationState:
        """Return the current bounded gate state for one session."""

        return self._session_states.get(
            session_id,
            SuperNovaSessionActivationState(session_id=session_id),
        )

    def get_attempt_log(
        self,
        session_id: str | None = None,
    ) -> tuple[SuperNovaActivationAttempt, ...]:
        """Return the recorded activation attempt log."""

        if session_id is not None:
            return tuple(self._attempts_by_session.get(session_id, ()))
        attempts: list[SuperNovaActivationAttempt] = []
        for session_attempts in self._attempts_by_session.values():
            attempts.extend(session_attempts)
        return tuple(attempts)

    def get_validation_log(
        self,
        session_id: str | None = None,
    ) -> tuple[SuperNovaActivationContextCheck, ...]:
        """Return activation-token validation checks."""

        if session_id is not None:
            return tuple(self._validation_checks_by_session.get(session_id, ()))
        checks: list[SuperNovaActivationContextCheck] = []
        for session_checks in self._validation_checks_by_session.values():
            checks.extend(session_checks)
        return tuple(checks)

    def get_trace(self, session_id: str | None = None) -> tuple[SuperNovaTraceEvent, ...]:
        """Return the visible Super Nova trace stream."""

        if session_id is not None:
            return tuple(self._trace_events_by_session.get(session_id, ()))
        events: list[SuperNovaTraceEvent] = []
        for session_events in self._trace_events_by_session.values():
            events.extend(session_events)
        return tuple(events)

    def get_active_token(self, session_id: str) -> ActivationToken | None:
        """Return the currently active token for one session, if any."""

        return self._active_tokens_by_session.get(session_id)

    def _record_attempt(
        self,
        session_id: str,
        attempt: SuperNovaActivationAttempt,
    ) -> None:
        attempts = list(self._attempts_by_session.get(session_id, ()))
        attempts.append(attempt)
        if len(attempts) > self.max_attempt_history:
            attempts = attempts[-self.max_attempt_history :]
        self._attempts_by_session[session_id] = attempts

    def _record_validation_check(
        self,
        session_id: str,
        check: SuperNovaActivationContextCheck,
    ) -> None:
        checks = list(self._validation_checks_by_session.get(session_id, ()))
        checks.append(check)
        if len(checks) > self.max_attempt_history:
            checks = checks[-self.max_attempt_history :]
        self._validation_checks_by_session[session_id] = checks

    def _record_trace_event(
        self,
        session_id: str,
        event: SuperNovaTraceEvent,
    ) -> None:
        events = list(self._trace_events_by_session.get(session_id, ()))
        events.append(event)
        if len(events) > self.max_attempt_history:
            events = events[-self.max_attempt_history :]
        self._trace_events_by_session[session_id] = events

    def _update_activity(self, session_id: str, activity: str) -> None:
        state = self._session_states.get(
            session_id,
            SuperNovaSessionActivationState(session_id=session_id),
        )
        self._session_states[session_id] = SuperNovaSessionActivationState(
            session_id=state.session_id,
            gate_status=state.gate_status,
            activation_token=state.activation_token,
            attempt_count=state.attempt_count,
            last_result=state.last_result,
            last_failure_reasons=state.last_failure_reasons,
            last_attempt_at_utc=state.last_attempt_at_utc,
            invalidated_tokens=state.invalidated_tokens,
            activation_reason=state.activation_reason,
            current_activity=activity,
            last_watchdog_result=state.last_watchdog_result,
            last_watchdog_reasons=state.last_watchdog_reasons,
            token_status=state.token_status,
        )

    def _invalidate_session_token(
        self,
        state: SuperNovaSessionActivationState,
        *,
        session_id: str,
        invalidated_token: str,
        failure_reasons: tuple[str, ...],
    ) -> SuperNovaSessionActivationState:
        invalidated_tokens = list(state.invalidated_tokens)
        if invalidated_token not in invalidated_tokens:
            invalidated_tokens.append(invalidated_token)
        token_record = self._active_tokens_by_session.get(session_id)
        if token_record is not None and token_record.token_id == invalidated_token:
            token_record.active = False
            self._active_tokens_by_session.pop(session_id, None)
        return SuperNovaSessionActivationState(
            session_id=state.session_id,
            gate_status="dormant",
            activation_token=None,
            attempt_count=state.attempt_count,
            last_result="fail",
            last_failure_reasons=failure_reasons,
            last_attempt_at_utc=datetime.now(UTC).isoformat(),
            invalidated_tokens=tuple(invalidated_tokens),
            activation_reason=state.activation_reason,
            current_activity="idle",
            last_watchdog_result="fail",
            last_watchdog_reasons=failure_reasons,
            token_status="inactive",
        )


def build_default_super_nova_activation_gate() -> SuperNovaActivationGate:
    """Return the default fail-closed activation gate."""

    return SuperNovaActivationGate()
