"""HTTP compatibility surface for the local Lawful Nova slice."""

from __future__ import annotations

import os
import json
import time
from uuid import uuid4
from dataclasses import dataclass
from typing import Any
import asyncio
import urllib.error
import urllib.request

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from nova.lawful_llm import LawfulLLM


@dataclass(frozen=True)
class ProviderResponse:
    content: str
    provider: str
    model: str
    input_tokens: int = 0
    output_tokens: int = 0


class OllamaChatProvider:
    provider_id = "ollama"

    def __init__(self, *, base_url: str, model: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model

    async def invoke(
        self,
        messages: list[dict[str, str]],
        *,
        model: str | None,
        max_tokens: int,
        temperature: float,
    ) -> ProviderResponse:
        return await asyncio.to_thread(
            self._invoke_sync,
            messages,
            model=model or self.model,
            max_tokens=max_tokens,
            temperature=temperature,
        )

    def _invoke_sync(
        self,
        messages: list[dict[str, str]],
        *,
        model: str,
        max_tokens: int,
        temperature: float,
    ) -> ProviderResponse:
        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {
                "num_predict": max_tokens,
                "temperature": temperature,
            },
        }
        request = urllib.request.Request(
            f"{self.base_url}/api/chat",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=float(os.environ.get("NOVA_OLLAMA_TIMEOUT", "120"))) as response:
                body = json.loads(response.read().decode("utf-8"))
        except urllib.error.URLError as exc:
            raise RuntimeError(f"Ollama provider unavailable at {self.base_url}: {exc}") from exc
        message = body.get("message") or {}
        text = str(message.get("content") or "")
        return ProviderResponse(
            content=text,
            provider=self.provider_id,
            model=str(body.get("model") or model),
            input_tokens=int(body.get("prompt_eval_count") or 0),
            output_tokens=int(body.get("eval_count") or 0),
        )


class ChatRequest(BaseModel):
    prompt: str = Field(min_length=1)
    tenant_id: str = "local"
    capability: str = "observe"


class OpenAIChatMessage(BaseModel):
    role: str
    content: Any = ""


class OpenAIChatCompletionRequest(BaseModel):
    model: str = "nova-local"
    messages: list[OpenAIChatMessage] = Field(default_factory=list)
    stream: bool = False
    tenant_id: str = "local"
    capability: str = "observe"


app = FastAPI(title="Local Lawful Nova API", version="0.1.0")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "nova_local_api"}


@app.post("/v1/chat")
def chat(request: ChatRequest) -> dict[str, Any]:
    return _run_lawful_chat(
        prompt=request.prompt,
        tenant_id=request.tenant_id,
        capability=request.capability,
    )


def _require_api_key(
    authorization: str | None = Header(default=None),
    x_api_key: str | None = Header(default=None),
) -> None:
    expected = os.environ.get("NOVA_API_KEY")
    if not expected:
        return
    bearer = ""
    if authorization and authorization.lower().startswith("bearer "):
        bearer = authorization[7:].strip()
    provided = bearer or (x_api_key or "").strip()
    if provided != expected:
        raise HTTPException(status_code=401, detail="invalid or missing Nova API key")


@app.get("/v1/models")
def openai_models(_: None = Depends(_require_api_key)) -> dict[str, Any]:
    return {
        "object": "list",
        "data": [
            {
                "id": "nova-local",
                "object": "model",
                "created": 0,
                "owned_by": "local-lawful-nova",
            }
        ],
    }


@app.post("/v1/chat/completions")
def openai_chat_completions(
    request: OpenAIChatCompletionRequest,
    _: None = Depends(_require_api_key),
) -> Any:
    prompt = _messages_to_prompt(request.messages)
    result = _run_lawful_chat(
        prompt=prompt,
        tenant_id=request.tenant_id,
        capability=request.capability,
    )
    completion = _openai_completion_payload(
        model=request.model,
        prompt=prompt,
        result=result,
    )
    if request.stream:
        return StreamingResponse(
            _stream_openai_completion(completion),
            media_type="text/event-stream",
        )
    return completion


def _run_lawful_chat(*, prompt: str, tenant_id: str, capability: str) -> dict[str, Any]:
    llm = LawfulLLM(
        operator_session_id="nova-local-api",
        signing_secret="local-api-secret",
        provider=_build_provider(),
    )
    turn = llm.ask(
        prompt,
        tenant_id=tenant_id,
        capability=capability,
    )
    return {
        "text": turn.text,
        "decision": turn.voss_runtime["decision"],
        "receipt": turn.receipt,
        "chain": _receipt_chain(turn.receipt),
        "receipt_verified": llm.verify_receipt(turn.receipt),
    }


def _build_provider() -> Any | None:
    provider = os.environ.get("NOVA_PROVIDER", "").strip().lower()
    if not provider:
        return None
    if provider != "ollama":
        raise RuntimeError(f"unsupported NOVA_PROVIDER: {provider}")
    return OllamaChatProvider(
        base_url=os.environ.get("NOVA_OLLAMA_BASE_URL", "http://127.0.0.1:11434"),
        model=os.environ.get("NOVA_OLLAMA_MODEL", "qwen2.5-coder:7b"),
    )


def _messages_to_prompt(messages: list[OpenAIChatMessage]) -> str:
    parts: list[str] = []
    for message in messages:
        content = _message_content_to_text(message.content)
        if content:
            parts.append(f"{message.role}: {content}")
    prompt = "\n".join(parts).strip()
    if not prompt:
        raise ValueError("messages must include at least one non-empty content field")
    return prompt


def _message_content_to_text(content: Any) -> str:
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        text_parts: list[str] = []
        for item in content:
            if isinstance(item, dict):
                if item.get("type") == "text":
                    text_parts.append(str(item.get("text") or ""))
                elif "text" in item:
                    text_parts.append(str(item["text"]))
            elif item is not None:
                text_parts.append(str(item))
        return "\n".join(part.strip() for part in text_parts if part and part.strip())
    if content is None:
        return ""
    return str(content).strip()


def _openai_completion_payload(*, model: str, prompt: str, result: dict[str, Any]) -> dict[str, Any]:
    completion_id = "chatcmpl-nova-" + uuid4().hex[:16]
    text = str(result["text"])
    return {
        "id": completion_id,
        "object": "chat.completion",
        "created": int(time.time()),
        "model": model or "nova-local",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": text,
                },
                "finish_reason": "stop",
            }
        ],
        "usage": {
            "prompt_tokens": _rough_token_count(prompt),
            "completion_tokens": _rough_token_count(text),
            "total_tokens": _rough_token_count(prompt) + _rough_token_count(text),
        },
        "nova": {
            "decision": result["decision"],
            "receipt": result["receipt"],
            "chain": result["chain"],
            "receipt_verified": result["receipt_verified"],
        },
    }


def _stream_openai_completion(completion: dict[str, Any]) -> Any:
    choice = completion["choices"][0]
    text = choice["message"]["content"]
    chunk_base = {
        "id": completion["id"],
        "object": "chat.completion.chunk",
        "created": completion["created"],
        "model": completion["model"],
    }
    yield _sse_data(
        {
            **chunk_base,
            "choices": [
                {
                    "index": 0,
                    "delta": {"role": "assistant", "content": text},
                    "finish_reason": None,
                }
            ],
            "nova": completion["nova"],
        }
    )
    yield _sse_data(
        {
            **chunk_base,
            "choices": [
                {
                    "index": 0,
                    "delta": {},
                    "finish_reason": "stop",
                }
            ],
        }
    )
    yield "data: [DONE]\n\n"


def _sse_data(payload: dict[str, Any]) -> str:
    return "data: " + json.dumps(payload, separators=(",", ":"), ensure_ascii=True) + "\n\n"


def _rough_token_count(value: str) -> int:
    return max(1, len(value.split()))


def _receipt_chain(receipt: dict[str, Any]) -> dict[str, Any]:
    payload = json.loads(str(receipt["payload"]))
    return {
        "identity": payload["identity"],
        "trace": payload["trace"],
        "authority_boundary": payload["authority_boundary"],
        "reproducibility": payload["reproducibility"],
    }


def main() -> None:
    import uvicorn

    port = int(os.environ.get("NOVA_PORT", "8080"))
    uvicorn.run("nova.api:app", host="127.0.0.1", port=port, log_level="info")


if __name__ == "__main__":
    main()
