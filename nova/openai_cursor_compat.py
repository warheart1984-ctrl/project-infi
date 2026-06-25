"""Normalize Cursor / OpenAI Chat Completions and Responses API payloads for Lawful Nova."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Any, Literal

from src.providers.http_chat_provider import extract_text_content

RequestKind = Literal["chat", "responses"]


@dataclass(slots=True)
class NormalizedOpenAIRequest:
    """Provider-ready OpenAI chat completion request."""

    kind: RequestKind
    model: str
    messages: list[dict[str, Any]]
    tools: list[dict[str, Any]] | None = None
    max_tokens: int | None = None
    max_completion_tokens: int | None = None
    temperature: float | None = None
    top_p: float | None = None
    stream: bool = False
    tenant_id: str = "local"
    capability: str = "observe"
    raw: dict[str, Any] = field(default_factory=dict)


def detect_request_kind(body: dict[str, Any]) -> RequestKind:
    if body.get("messages"):
        return "chat"
    if body.get("input") is not None:
        return "responses"
    return "chat"


def _content_to_text(content: Any) -> str:
    return extract_text_content(content)


def normalize_input_to_messages(input_value: Any) -> list[dict[str, Any]]:
    if isinstance(input_value, str):
        return [{"role": "user", "content": input_value}]
    if not isinstance(input_value, list):
        return [{"role": "user", "content": str(input_value or "")}]
    messages: list[dict[str, Any]] = []
    for item in input_value:
        if isinstance(item, str):
            messages.append({"role": "user", "content": item})
            continue
        if not isinstance(item, dict):
            continue
        role = str(item.get("role") or item.get("type") or "user")
        if role in {"message", "input_text"}:
            role = "user"
        content = item.get("content")
        if content is None and "text" in item:
            content = item.get("text")
        messages.append({"role": role, "content": _content_to_text(content)})
    return messages or [{"role": "user", "content": "Hello."}]


def normalize_tools(tools: Any) -> list[dict[str, Any]] | None:
    if not tools:
        return None
    if not isinstance(tools, list):
        return None
    normalized: list[dict[str, Any]] = []
    for tool in tools:
        if not isinstance(tool, dict):
            continue
        if tool.get("type") == "function" and isinstance(tool.get("function"), dict):
            normalized.append(tool)
            continue
        name = tool.get("name") or tool.get("id")
        if not name:
            continue
        parameters = tool.get("parameters") or tool.get("input_schema") or {"type": "object", "properties": {}}
        normalized.append(
            {
                "type": "function",
                "function": {
                    "name": str(name),
                    "description": str(tool.get("description") or ""),
                    "parameters": parameters,
                },
            }
        )
    return normalized or None


def normalize_request(body: dict[str, Any]) -> NormalizedOpenAIRequest:
    kind = detect_request_kind(body)
    if kind == "responses":
        messages = normalize_input_to_messages(body.get("input"))
    else:
        raw_messages = body.get("messages") or []
        messages = []
        for item in raw_messages:
            if not isinstance(item, dict):
                continue
            messages.append(
                {
                    "role": str(item.get("role") or "user"),
                    "content": item.get("content"),
                }
            )
        if not messages:
            messages = [{"role": "user", "content": "Hello."}]

    max_tokens = body.get("max_tokens") or body.get("max_output_tokens")
    max_completion = body.get("max_completion_tokens")
    if max_completion is not None:
        try:
            max_completion = int(max_completion)
        except (TypeError, ValueError):
            max_completion = None
    if max_tokens is not None:
        try:
            max_tokens = int(max_tokens)
        except (TypeError, ValueError):
            max_tokens = None

    temperature = body.get("temperature")
    if temperature is not None:
        try:
            temperature = float(temperature)
        except (TypeError, ValueError):
            temperature = None

    top_p = body.get("top_p")
    if top_p is not None:
        try:
            top_p = float(top_p)
        except (TypeError, ValueError):
            top_p = None

    return NormalizedOpenAIRequest(
        kind=kind,
        model=str(body.get("model") or "lawful-nova"),
        messages=messages,
        tools=normalize_tools(body.get("tools")),
        max_tokens=max_tokens,
        max_completion_tokens=max_completion,
        temperature=temperature,
        top_p=top_p,
        stream=bool(body.get("stream")),
        tenant_id=str(body.get("tenant_id") or "local"),
        capability=str(body.get("capability") or "observe"),
        raw=body,
    )


def extract_user_prompt(messages: list[dict[str, Any]]) -> str:
    for message in reversed(messages):
        if str(message.get("role", "")).lower() == "user":
            text = _content_to_text(message.get("content"))
            if text.strip():
                return text.strip()
    for message in reversed(messages):
        text = _content_to_text(message.get("content"))
        if text.strip():
            return text.strip()
    return "Hello."


def build_chat_completion_response(
    *,
    model: str,
    content: str,
    finish_reason: str = "stop",
    tool_calls: list[dict[str, Any]] | None = None,
    prompt_tokens: int | None = None,
    completion_tokens: int | None = None,
) -> dict[str, Any]:
    prompt_tokens = prompt_tokens or max(1, len(content.split()) // 2)
    completion_tokens = completion_tokens or max(1, len(content.split()))
    message: dict[str, Any] = {"role": "assistant", "content": content}
    if tool_calls:
        message["tool_calls"] = tool_calls
    return {
        "id": f"chatcmpl-nova-{int(time.time() * 1000)}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": model,
        "choices": [
            {
                "index": 0,
                "message": message,
                "finish_reason": finish_reason,
            }
        ],
        "usage": {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens,
        },
    }


def build_responses_api_response(*, model: str, content: str) -> dict[str, Any]:
    return {
        "id": f"resp-nova-{int(time.time() * 1000)}",
        "object": "response",
        "created_at": int(time.time()),
        "model": model,
        "status": "completed",
        "output": [
            {
                "type": "message",
                "id": f"msg-nova-{int(time.time() * 1000)}",
                "role": "assistant",
                "status": "completed",
                "content": [{"type": "output_text", "text": content}],
            }
        ],
        "usage": {
            "input_tokens": max(1, len(content.split()) // 2),
            "output_tokens": max(1, len(content.split())),
            "total_tokens": max(2, len(content.split())),
        },
    }


def format_sse_chat_chunk(
    *,
    chunk_id: str,
    model: str,
    delta: dict[str, Any],
    finish_reason: str | None = None,
) -> str:
    payload: dict[str, Any] = {
        "id": chunk_id,
        "object": "chat.completion.chunk",
        "created": int(time.time()),
        "model": model,
        "choices": [
            {
                "index": 0,
                "delta": delta,
                "finish_reason": finish_reason,
            }
        ],
    }
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


def format_sse_done() -> str:
    return "data: [DONE]\n\n"


def lawful_receipt_header_payload(
    *,
    turn_receipt: dict[str, Any],
    voss_runtime: dict[str, Any],
    law_kernel: dict[str, Any],
    receipt_verified: bool,
    chain: dict[str, Any],
) -> str:
    return json.dumps(
        {
            "decision": voss_runtime.get("decision"),
            "law_kernel": law_kernel,
            "receipt": turn_receipt,
            "chain": chain,
            "receipt_verified": receipt_verified,
        },
        ensure_ascii=False,
    )
