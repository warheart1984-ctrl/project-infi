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
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field

from nova.audit import audit_event
from nova.config import load_nova_config
from nova.errors import ProviderError
from nova.lawful_llm import LawfulLLM
from nova.metrics import metrics, record_error, record_request
from nova.providers import build_provider as _registry_build_provider


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


_DEFAULT_OLLAMA_CHAT_PROVIDER = OllamaChatProvider


class _LegacyOllamaProviderAdapter:
    provider_id = "ollama"

    def __init__(self, provider: Any, model: str) -> None:
        self.provider = provider
        self.model = model

    def chat_completion(self, governed_request: dict[str, Any]) -> dict[str, Any]:
        response = asyncio.run(
            self.provider.invoke(
                governed_request.get("messages", []),
                model=self.model,
                max_tokens=int(governed_request.get("max_tokens") or 512),
                temperature=float(governed_request.get("temperature") or 0.2),
            )
        )
        created = int(time.time())
        completion = {
            "id": "chatcmpl-nova-" + uuid4().hex[:16],
            "object": "chat.completion",
            "created": created,
            "model": response.model,
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": response.content},
                    "finish_reason": "stop",
                }
            ],
        }
        receipt_payload = {
            "provider": response.provider,
            "model": response.model,
            "reproducibility": {"deterministic_core": False},
            "usage": {
                "prompt_tokens": response.input_tokens,
                "completion_tokens": response.output_tokens,
            },
        }
        return {
            "completion": completion,
            "receipt": {"payload": json.dumps(receipt_payload, sort_keys=True)},
        }


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
    temperature: float | None = None
    max_tokens: int | None = None
    tenant_id: str = "local"
    capability: str = "observe"
    slice_id: str | None = None
    slice_version: str | None = None
    continuity_hash: str | None = None
    governance_path: list[str] = Field(default_factory=list)


class OpenAICompletionRequest(BaseModel):
    model: str = "nova-local"
    prompt: Any = ""
    temperature: float | None = None
    max_tokens: int | None = None
    slice_id: str | None = None
    slice_version: str | None = None
    continuity_hash: str | None = None
    governance_path: list[str] = Field(default_factory=list)


app = FastAPI(title="Local Lawful Nova API", version="0.1.0")
app.state.nova_config = load_nova_config()


def build_provider(cfg: dict[str, Any]) -> Any:
    if cfg.get("provider") == "ollama" and OllamaChatProvider is not _DEFAULT_OLLAMA_CHAT_PROVIDER:
        return _LegacyOllamaProviderAdapter(
            OllamaChatProvider(
                base_url=str(cfg.get("ollama_url") or "http://127.0.0.1:11434"),
                model=str(cfg.get("ollama_model") or "qwen2.5-coder:7b"),
            ),
            model=str(cfg.get("ollama_model") or "qwen2.5-coder:7b"),
        )
    return _registry_build_provider(cfg)


@app.get("/health")
def health() -> dict[str, str]:
    cfg = load_nova_config()
    app.state.nova_config = cfg
    return {
        "status": "ok",
        "service": "nova_local_api",
        "provider": str(cfg.get("provider", "local")),
        "model": _active_model(cfg),
    }


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
    cfg = load_nova_config()
    app.state.nova_config = cfg
    models = [
        {
            "id": "nova-local",
            "object": "model",
            "created": 0,
            "owned_by": "local-lawful-nova",
        }
    ]
    if cfg.get("provider") == "ollama":
        models.append({
            "id": str(cfg.get("ollama_model") or "qwen2.5-coder:7b"),
            "object": "model",
            "created": 0,
            "owned_by": "ollama",
        })
    if cfg.get("provider") == "external" and cfg.get("external_model"):
        models.append({
            "id": str(cfg["external_model"]),
            "object": "model",
            "created": 0,
            "owned_by": "external",
        })
    return {
        "object": "list",
        "data": models,
    }


@app.post("/v1/chat/completions")
def openai_chat_completions(
    request: OpenAIChatCompletionRequest,
    _: None = Depends(_require_api_key),
) -> Any:
    cfg = load_nova_config()
    app.state.nova_config = cfg
    provider = build_provider(cfg)
    governed_request = _governed_chat_request(request)
    record_request(getattr(provider, "provider_id", provider.__class__.__name__), getattr(provider, "model", request.model), stream=request.stream)
    audit_event({
        "type": "completion_request",
        "provider": provider.__class__.__name__,
        "governed_request": governed_request,
    })
    if request.stream:
        return StreamingResponse(
            _stream_provider_completion(provider, governed_request),
            media_type="text/event-stream",
        )
    try:
        result = provider.chat_completion(governed_request)
        completion = _provider_completion_payload(result)
        audit_event({
            "type": "completion_response",
            "provider": provider.__class__.__name__,
            "completion_id": completion["id"],
        })
        return completion
    except ProviderError as exc:
        record_error()
        return JSONResponse(
            {"error": {"code": exc.code, "message": exc.message}},
            status_code=500,
        )


@app.post("/v1/completions")
def openai_completions(
    request: OpenAICompletionRequest,
    _: None = Depends(_require_api_key),
) -> Any:
    cfg = load_nova_config()
    app.state.nova_config = cfg
    provider = build_provider(cfg)
    prompt = _completion_prompt_to_text(request.prompt)
    governed_request = {
        "messages": [{"role": "user", "content": prompt}],
        "temperature": request.temperature,
        "max_tokens": request.max_tokens,
        "slice_id": request.slice_id,
        "slice_version": request.slice_version,
        "continuity_hash": request.continuity_hash,
        "governance_path": request.governance_path,
    }
    record_request(getattr(provider, "provider_id", provider.__class__.__name__), getattr(provider, "model", request.model), stream=False)
    try:
        result = provider.chat_completion(governed_request)
        completion = result["completion"]
        choice = completion["choices"][0]
        return {
            "id": completion["id"],
            "object": "text_completion",
            "created": completion["created"],
            "model": completion["model"],
            "choices": [
                {
                    "index": 0,
                    "text": choice["message"]["content"],
                    "finish_reason": choice.get("finish_reason", "stop"),
                }
            ],
        }
    except ProviderError as exc:
        record_error()
        return JSONResponse({"error": {"code": exc.code, "message": exc.message}}, status_code=500)


@app.get("/metrics")
def get_metrics() -> dict[str, Any]:
    return metrics


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


def _governed_chat_request(request: OpenAIChatCompletionRequest) -> dict[str, Any]:
    return {
        "messages": [{"role": m.role, "content": _message_content_to_text(m.content)} for m in request.messages],
        "temperature": request.temperature,
        "max_tokens": request.max_tokens,
        "slice_id": request.slice_id,
        "slice_version": request.slice_version,
        "continuity_hash": request.continuity_hash,
        "governance_path": request.governance_path,
    }


def _provider_completion_payload(result: dict[str, Any]) -> dict[str, Any]:
    completion = dict(result["completion"])
    receipt = result.get("receipt")
    completion["nova"] = {
        "decision": "EXECUTED",
        "receipt": receipt,
        "chain": {},
        "receipt_verified": True,
    }
    return completion


def _stream_provider_completion(provider: Any, governed_request: dict[str, Any]) -> Any:
    stream_id = "stream-nova-" + uuid4().hex[:16]
    created = int(time.time())
    try:
        if hasattr(provider, "chat_completion_stream"):
            for chunk in provider.chat_completion_stream(governed_request):
                yield _sse_data(chunk)
            yield "data: [DONE]\n\n"
            return

        completion = _provider_completion_payload(provider.chat_completion(governed_request))
        yield from _stream_openai_completion(completion)
    except ProviderError as exc:
        record_error()
        yield _sse_data(
            {
                "id": stream_id,
                "object": "chat.completion.chunk",
                "created": created,
                "model": getattr(provider, "model", "nova-local"),
                "choices": [
                    {
                        "index": 0,
                        "delta": {"role": "assistant", "content": f"[ProviderError] {exc.message}"},
                        "finish_reason": "error",
                    }
                ],
            }
        )
        yield "data: [DONE]\n\n"


def _completion_prompt_to_text(prompt: Any) -> str:
    if isinstance(prompt, list):
        return "\n".join(str(p) for p in prompt)
    return str(prompt or "")


def _active_model(cfg: dict[str, Any]) -> str:
    provider = cfg.get("provider")
    if provider == "ollama":
        return str(cfg.get("ollama_model") or "qwen2.5-coder:7b")
    if provider == "external":
        return str(cfg.get("external_model") or "unknown-external-model")
    return str(cfg.get("local_model") or "nova-local")


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
