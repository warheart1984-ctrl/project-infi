from __future__ import annotations

import time
from uuid import uuid4
from typing import Any

from nova.receipts import make_receipt


class LocalDeterministicProvider:
    provider_id = "local"

    def __init__(self, model: str = "nova-local") -> None:
        self.model = model

    def chat_completion(self, governed_request: dict[str, Any]) -> dict[str, Any]:
        prompt = _last_message(governed_request)
        content = f"Under RSL, Nova Cortex reads {prompt.lower()} with no matching LSG facts."
        completion = {
            "id": f"local-{uuid4()}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": self.model,
            "choices": [
                {
                    "index": 0,
                    "finish_reason": "stop",
                    "message": {"role": "assistant", "content": content},
                }
            ],
        }
        receipt = make_receipt(
            provider="local",
            model=self.model,
            governed_request=governed_request,
            raw_provider_response={"content": content},
            normalized_completion=completion,
            deterministic_core=True,
            rsl_version="1.0",
            slice_id=governed_request.get("slice_id"),
            slice_version=governed_request.get("slice_version"),
            continuity_hash=governed_request.get("continuity_hash"),
            governance_path=governed_request.get("governance_path", []),
        )
        return {"completion": completion, "receipt": receipt}


def _last_message(governed_request: dict[str, Any]) -> str:
    messages = governed_request.get("messages") or []
    if messages:
        return str(messages[-1].get("content") or "the request")
    return str(governed_request.get("prompt") or "the request")
