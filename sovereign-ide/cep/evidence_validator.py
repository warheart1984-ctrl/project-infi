from __future__ import annotations

from .config import MIN_EVIDENCE_ITEMS
from .models import EvidenceResult, PromotionRequest
from .queues import AUDIT_OUT, EVIDENCE_JOBS, Queue


def enqueue_evidence_jobs(queue: Queue, requests: list[PromotionRequest]) -> None:
    for request in requests:
        queue.publish(EVIDENCE_JOBS, request)


def run_evidence_validator(queue: Queue) -> list[EvidenceResult]:
    results: list[EvidenceResult] = []
    for request in queue.drain(EVIDENCE_JOBS):
        passed = len(request.evidence_sample) >= MIN_EVIDENCE_ITEMS
        result = EvidenceResult(
            request_id=request.request_id,
            passed=passed,
            details={
                "count": len(request.evidence_sample),
                "minimum": MIN_EVIDENCE_ITEMS,
                "sources": sorted({str(item.get("source", "")) for item in request.evidence_sample if str(item.get("source", ""))}),
            },
        )
        queue.publish(AUDIT_OUT, result)
        results.append(result)
    return results
