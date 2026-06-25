"""ExecutionSpanManager — ephemeral span and trace storage (TS mirror)."""

from __future__ import annotations

import time
import uuid
from dataclasses import replace

from governed_memory.types import ExecutionSpan, ExecutionSpanState, ExecutionTrace


class ExecutionSpanManager:
    def __init__(self) -> None:
        self._spans: dict[str, ExecutionSpan] = {}

    def start_span(
        self,
        *,
        intent_version: int,
        authority_token_id: str,
        parent_span: str | None = None,
    ) -> ExecutionSpan:
        span = ExecutionSpan(
            span_id=str(uuid.uuid4()),
            parent_span=parent_span,
            intent_version=intent_version,
            authority_token_id=authority_token_id,
            start_time=time.time() * 1000,
            state="active",
            trace=[],
        )
        self._spans[span.span_id] = span
        return span

    def get(self, span_id: str) -> ExecutionSpan | None:
        return self._spans.get(span_id)

    def record_trace(self, span_id: str, step: ExecutionTrace) -> ExecutionSpan:
        span = self._spans.get(span_id)
        if not span:
            raise ValueError(f"unknown span: {span_id}")
        if span.state != "active":
            raise ValueError(f"span not active: {span.state}")
        if not step.justification.strip():
            raise ValueError("EXECUTION_UNGOVERNED: trace step requires justification")
        if (
            step.references.intent_version != span.intent_version
            or step.references.authority_token_id != span.authority_token_id
        ):
            raise ValueError("EXECUTION_UNGOVERNED: trace references mismatch span bindings")
        updated = replace(span, trace=[*span.trace, step])
        self._spans[span_id] = updated
        return updated

    def complete(self, span_id: str) -> ExecutionSpan:
        return self._terminal(span_id, "completed")

    def terminate(self, span_id: str) -> ExecutionSpan:
        return self._terminal(span_id, "terminated")

    def fault(self, span_id: str) -> ExecutionSpan:
        return self._terminal(span_id, "faulted")

    def _terminal(self, span_id: str, state: ExecutionSpanState) -> ExecutionSpan:
        span = self._spans.get(span_id)
        if not span:
            raise ValueError(f"unknown span: {span_id}")
        updated = replace(span, state=state)
        self._spans[span_id] = updated
        return updated
