from __future__ import annotations

from .config import MIN_LINEAGE_DEPTH
from .models import LineageResult, PromotionRequest
from .queues import AUDIT_OUT, LINEAGE_JOBS, Queue


def enqueue_lineage_jobs(queue: Queue, requests: list[PromotionRequest]) -> None:
    for request in requests:
        queue.publish(LINEAGE_JOBS, request)


def run_lineage_validator(queue: Queue) -> list[LineageResult]:
    results: list[LineageResult] = []
    for request in queue.drain(LINEAGE_JOBS):
        timestamps = [int(item.get("timestamp", 0) or 0) for item in request.lineage_sample]
        continuity = all(left <= right for left, right in zip(timestamps, timestamps[1:]))
        passed = len(request.lineage_sample) >= MIN_LINEAGE_DEPTH and continuity
        result = LineageResult(
            request_id=request.request_id,
            passed=passed,
            details={
                "depth": len(request.lineage_sample),
                "minimum": MIN_LINEAGE_DEPTH,
                "continuity": continuity,
            },
        )
        queue.publish(AUDIT_OUT, result)
        results.append(result)
    return results
