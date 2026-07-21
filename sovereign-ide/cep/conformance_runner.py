from __future__ import annotations

from typing import Protocol

from .models import ConformanceResult, PromotionRequest
from .queues import AUDIT_OUT, CONFORMANCE_JOBS, Queue


class _Constitution(Protocol):
    def validate(self, agent_state: dict[str, object]) -> bool: ...


def enqueue_conformance_jobs(queue: Queue, requests: list[PromotionRequest]) -> None:
    for request in requests:
        queue.publish(CONFORMANCE_JOBS, request)


def run_conformance_runner(queue: Queue, constitution: _Constitution) -> list[ConformanceResult]:
    results: list[ConformanceResult] = []
    for request in queue.drain(CONFORMANCE_JOBS):
        passed = constitution.validate(dict(request.snapshot))
        result = ConformanceResult(
            request_id=request.request_id,
            passed=passed,
            details={
                "snapshot": dict(request.snapshot),
                "constitution": getattr(constitution, "list_ids", lambda: [])(),
            },
        )
        queue.publish(AUDIT_OUT, result)
        results.append(result)
    return results
