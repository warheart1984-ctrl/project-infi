from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .queues import AUDIT_OUT, DECISIONS_OUT, Queue


@dataclass
class CEPClient:
    source: Any

    def _queue(self) -> Queue | None:
        if isinstance(self.source, Queue):
            return self.source
        queue = getattr(self.source, "queue", None)
        if isinstance(queue, Queue):
            return queue
        return queue

    def list_decisions(self) -> list[Any]:
        decision_log = getattr(self.source, "decision_log", None)
        if decision_log is not None:
            return list(decision_log)
        queue = self._queue()
        if queue is None:
            return []
        return list(queue.consume(DECISIONS_OUT))

    def list_audit_events(self) -> list[Any]:
        governance = getattr(self.source, "governance", None)
        audit_log = getattr(governance, "audit_log", None)
        if audit_log is not None:
            return list(audit_log)
        queue = self._queue()
        if queue is None:
            return []
        return list(queue.consume(AUDIT_OUT))
