"""Deterministic governance replay for completed execution spans."""

from __future__ import annotations

from governed_memory.authority_ledger import AuthorityLedger
from governed_memory.execution_memory import ExecutionSpanManager
from governed_memory.governance_enforcement import GovernanceEnforcementEngine
from governed_memory.intent_ledger import IntentLedger
from governed_memory.types import GovernanceViolation, ReplayResult


def _violation_from_error(exc: Exception, *, step_index: int | None = None) -> GovernanceViolation:
    msg = str(exc)
    code = msg.split(":", 1)[0] if ":" in msg else "REPLAY_FAILED"
    return GovernanceViolation(code=code, message=msg, step_index=step_index)


def replay(
    span_id: str,
    *,
    span_manager: ExecutionSpanManager,
    intent_ledger: IntentLedger,
    authority_ledger: AuthorityLedger,
    governance: GovernanceEnforcementEngine | None = None,
) -> ReplayResult:
    """Re-validate governance invariants for a span's recorded trace (no side effects)."""
    engine = governance or GovernanceEnforcementEngine(intent_ledger, authority_ledger)
    span = span_manager.get(span_id)
    if not span:
        return ReplayResult(
            success=False,
            violations=[
                GovernanceViolation(
                    code="SPAN_NOT_FOUND",
                    message=f"unknown span: {span_id}",
                )
            ],
        )

    if span.state not in ("completed", "terminated", "active"):
        return ReplayResult(
            success=False,
            violations=[
                GovernanceViolation(
                    code="SPAN_STATE",
                    message=f"cannot replay span in state {span.state}",
                    span_id=span_id,
                )
            ],
        )

    violations: list[GovernanceViolation] = []
    for index, step in enumerate(span.trace):
        try:
            engine.validate_trace_step(step)
        except ValueError as exc:
            violations.append(_violation_from_error(exc, step_index=index))

    if violations:
        return ReplayResult(
            success=False,
            violations=violations,
            step_index=violations[0].step_index,
        )

    return ReplayResult(success=True, violations=[])
