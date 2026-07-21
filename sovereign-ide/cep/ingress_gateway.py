from __future__ import annotations

from uuid import uuid4

from .models import PromotionRequest
from .queues import PROMOTIONS_IN, Queue


def handle_promotion_request(json_payload: dict, queue: Queue) -> PromotionRequest:
    request = PromotionRequest(
        request_id=str(uuid4()),
        agent_id=str(json_payload["agent_id"]),
        snapshot=dict(json_payload.get("snapshot", {})),
        evidence_sample=[dict(item) for item in json_payload.get("evidence_sample", [])],
        lineage_sample=[dict(item) for item in json_payload.get("lineage_sample", [])],
        requested_change=dict(json_payload["requested_change"]),
    )
    queue.publish(PROMOTIONS_IN, request)
    return request
