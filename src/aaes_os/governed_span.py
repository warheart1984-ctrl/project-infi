"""Governed span state machine."""

from __future__ import annotations

from uuid import uuid4

from src.aaes_os.errors import AaesOsValidationError
from src.aaes_os.models import RuntimeContext
from src.aaes_os.types import SpanState


class GovernedSpan:
    """Engineering: GovernedSpanEngine span handle."""

    def __init__(
        self,
        *,
        span_id: str | None = None,
        runtime_context: RuntimeContext | None = None,
        parent_span_id: str | None = None,
    ) -> None:
        self.span_id = span_id or f"span_{uuid4().hex}"
        self.parent_span_id = parent_span_id
        self.runtime_context = runtime_context
        self.state = SpanState.INIT
        self._csr_registered = False

    def _sync_csr(self, new_state: SpanState, *, receipt_id: str | None = None) -> None:
        try:
            from src.aaes_os.csr_bridge import get_aais_csr, register_cognitive_span, sync_span_state_to_csr

            csr = get_aais_csr()
            if not self._csr_registered:
                register_cognitive_span(csr, self.span_id)
                self._csr_registered = True
            sync_span_state_to_csr(csr, self.span_id, new_state, receipt_id=receipt_id)
        except Exception:
            pass  # observability-only

    def close(self) -> None:
        if self.state not in {SpanState.RESULTED, SpanState.CLOSED}:
            raise AaesOsValidationError(
                "AAES_SPAN_STATE_INVALID",
                f"cannot close span in state {self.state.value}",
            )
        self.state = SpanState.CLOSED
        self._sync_csr(SpanState.CLOSED)

    def _transition(self, new_state: SpanState) -> None:
        self.state = new_state
        self._sync_csr(new_state)
