from __future__ import annotations

import json
import time
from typing import Any, Iterator
from uuid import uuid4

from nova.errors import ProviderError
from nova.receipts import make_receipt
from .http import post_json, post_json_lines


class OllamaProvider:
    provider_id = "ollama"

    def __init__(
        self,
        *,
        base_url: str = "http://127.0.0.1:11434",
        model: str = "qwen2.5-coder:3b",
        timeout: float = 60,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout

    def _ollama_url(self) -> str:
        return f"{self.base_url}/api/chat"

    def chat_completion(self, governed_request: dict[str, Any]) -> dict[str, Any]:
        payload = self._payload(governed_request, stream=False)
        try:
            data = post_json(self._ollama_url(), payload, timeout=self.timeout)
        except ProviderError:
            raise
        except Exception as exc:
            raise ProviderError(code="OLLAMA_REQUEST_FAILED", message=str(exc)) from exc
        content = str((data.get("message") or {}).get("content") or "")
        completion = self._completion(content=content, completion_id=f"ollama-{uuid4()}")
        receipt = make_receipt(
            provider="ollama",
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

    def chat_completion_stream(self, governed_request: dict[str, Any]) -> Iterator[dict[str, Any]]:
        payload = self._payload(governed_request, stream=True)
        stream_id = f"ollama-stream-{uuid4()}"
        created = int(time.time())
        full_content = ""
        for line in post_json_lines(self._ollama_url(), payload, timeout=self.timeout):
            content = self._stream_content(line)
            if not content:
                continue
            full_content += content
            yield {
                "id": stream_id,
                "object": "chat.completion.chunk",
                "created": created,
                "model": self.model,
                "choices": [
                    {
                        "index": 0,
                        "delta": {"role": "assistant", "content": content},
                        "finish_reason": None,
                    }
                ],
            }
        completion = self._completion(content=full_content, completion_id=stream_id, created=created)
        receipt = make_receipt(
            provider="ollama",
            model=self.model,
            governed_request=governed_request,
            raw_provider_response={"stream": True, "content": full_content},
            normalized_completion=completion,
            deterministic_core=False,
            rsl_version="1.0",
            slice_id=governed_request.get("slice_id"),
            slice_version=governed_request.get("slice_version"),
            continuity_hash=governed_request.get("continuity_hash"),
            governance_path=governed_request.get("governance_path", []),
        )
        yield {"completion": completion, "receipt": receipt}

    def _payload(self, governed_request: dict[str, Any], *, stream: bool) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": governed_request.get("messages", []),
            "stream": stream,
        }
        options: dict[str, Any] = {}
        if governed_request.get("temperature") is not None:
            options["temperature"] = governed_request["temperature"]
        if governed_request.get("max_tokens") is not None:
            options["num_predict"] = governed_request["max_tokens"]
        if options:
            payload["options"] = options
        return payload

    def _completion(self, *, content: str, completion_id: str, created: int | None = None) -> dict[str, Any]:
        return {
            "id": completion_id,
            "object": "chat.completion",
            "created": created or int(time.time()),
            "model": self.model,
            "choices": [
                {
                    "index": 0,
                    "finish_reason": "stop",
                    "message": {"role": "assistant", "content": content},
                }
            ],
        }

    def _stream_content(self, line: bytes) -> str:
        try:
            data = json.loads(line.decode("utf-8"))
            return str((data.get("message") or {}).get("content") or data.get("response") or "")
        except Exception:
            return line.decode("utf-8", errors="ignore")
