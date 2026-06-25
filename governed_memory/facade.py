"""Operator-facing façades over governed memory strata."""

from __future__ import annotations

import time

from governed_memory.authority_ledger import AuthorityLedger
from governed_memory.execution_memory import ExecutionSpanManager
from governed_memory.governance_enforcement import GovernanceEnforcementEngine
from governed_memory.intent_ledger import IntentLedger
from governed_memory.replay import replay as replay_span
from governed_memory.types import (
    AuthorityScope,
    AuthorityToken,
    ExecutionSpan,
    ExecutionTrace,
    IntentHorizon,
    IntentRecord,
    ReplayResult,
    TraceReferences,
    TraceStepType,
)

_DEFAULT_INTENT_LEDGER = IntentLedger()
_DEFAULT_AUTHORITY_LEDGER = AuthorityLedger()
_DEFAULT_SPAN_MANAGER = ExecutionSpanManager()
_DEFAULT_GOVERNANCE = GovernanceEnforcementEngine(
    _DEFAULT_INTENT_LEDGER,
    _DEFAULT_AUTHORITY_LEDGER,
)


def create_intent(
    goal: str,
    constraints: list[str],
    operator_key: str,
    *,
    success_criteria: list[str] | None = None,
    horizon: IntentHorizon = "short",
    intent_ledger: IntentLedger | None = None,
) -> IntentRecord:
    ledger = intent_ledger or _DEFAULT_INTENT_LEDGER
    return ledger.append(
        operator_id=operator_key,
        semantic_goal=goal,
        constraints=list(constraints),
        success_criteria=list(success_criteria or []),
        horizon=horizon,
        signature=operator_key,
    )


def issue_authority(
    intent_version: int,
    capabilities: list[str],
    gov_key: str,
    *,
    issued_to: str = "executor",
    resources: list[str] | None = None,
    time_limit_ms: float = 60_000.0,
    authority_ledger: AuthorityLedger | None = None,
) -> AuthorityToken:
    ledger = authority_ledger or _DEFAULT_AUTHORITY_LEDGER
    return ledger.issue(
        issued_by=gov_key,
        issued_to=issued_to,
        capabilities=capabilities,
        scope=AuthorityScope(
            resources=resources or ["*"],
            time_limit_ms=time.time() * 1000 + time_limit_ms,
            intent_version=intent_version,
        ),
    )


def start_span(
    intent_version: int,
    authority_token_id: str,
    *,
    parent_span: str | None = None,
    span_manager: ExecutionSpanManager | None = None,
) -> ExecutionSpan:
    manager = span_manager or _DEFAULT_SPAN_MANAGER
    return manager.start_span(
        intent_version=intent_version,
        authority_token_id=authority_token_id,
        parent_span=parent_span,
    )


def validate_step(
    step: ExecutionTrace,
    *,
    governance: GovernanceEnforcementEngine | None = None,
) -> None:
    engine = governance or _DEFAULT_GOVERNANCE
    engine.validate_trace_step(step)


def complete_span(
    span_id: str,
    *,
    span_manager: ExecutionSpanManager | None = None,
) -> ExecutionSpan:
    manager = span_manager or _DEFAULT_SPAN_MANAGER
    return manager.complete(span_id)


def record_trace(
    span_id: str,
    *,
    step_type: TraceStepType,
    content: str,
    justification: str,
    intent_version: int,
    authority_token_id: str,
    span_manager: ExecutionSpanManager | None = None,
    governance: GovernanceEnforcementEngine | None = None,
) -> ExecutionSpan:
    manager = span_manager or _DEFAULT_SPAN_MANAGER
    step = ExecutionTrace(
        timestamp=time.time() * 1000,
        step_type=step_type,
        content=content,
        justification=justification,
        references=TraceReferences(
            intent_version=intent_version,
            authority_token_id=authority_token_id,
        ),
    )
    validate_step(step, governance=governance)
    return manager.record_trace(span_id, step)


def replay(
    span_id: str,
    *,
    span_manager: ExecutionSpanManager | None = None,
    intent_ledger: IntentLedger | None = None,
    authority_ledger: AuthorityLedger | None = None,
    governance: GovernanceEnforcementEngine | None = None,
) -> ReplayResult:
    return replay_span(
        span_id,
        span_manager=span_manager or _DEFAULT_SPAN_MANAGER,
        intent_ledger=intent_ledger or _DEFAULT_INTENT_LEDGER,
        authority_ledger=authority_ledger or _DEFAULT_AUTHORITY_LEDGER,
        governance=governance,
    )
