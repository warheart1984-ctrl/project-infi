from __future__ import annotations

import time
from typing import Any
from uuid import uuid4

from nova.errors import ProviderError
from nova.receipts import make_receipt
from .http import post_json


class ExternalProvider:
    provider_id = "external"

    def __init__(self, *, base_url: str, api_key: str | None, model: str, timeout: float = 60) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.timeout = timeout

    def chat_completion(self, governed_request: dict[str, Any]) -> dict[str, Any]:
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        payload = {
            "model": self.model,
            "messages": governed_request.get("messages", []),
            "temperature": governed_request.get("temperature"),
            "max_tokens": governed_request.get("max_tokens"),
        }
        try:
            data = post_json(f"{self.base_url}/chat/completions", payload, headers=headers, timeout=self.timeout)
        except ProviderError:
            raise
        except Exception as exc:
            raise ProviderError(code="EXTERNAL_REQUEST_FAILED", message=str(exc)) from exc
        completion = {
            "id": data.get("id", f"external-{uuid4()}"),
            "object": "chat.completion",
            "created": data.get("created", int(time.time())),
            "model": data.get("model", self.model),
            "choices": data.get("choices", []),
        }
        receipt = make_receipt(
            provider="external",
            model=self.model,
            governed_request=governed_request,
            raw_provider_response=data,
            normalized_completion=completion,
            deterministic_core=False,
            rsl_version="1.0",
            slice_id=governed_request.get("slice_id"),
            slice_version=governed_request.get("slice_version"),
            continuity_hash=governed_request.get("continuity_hash"),
            governance_path=governed_request.get("governance_path", []),
        )
        return {"completion": completion, "receipt": receipt}
