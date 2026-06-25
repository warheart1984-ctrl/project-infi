"""OpenAI-compatible route handlers for Lawful Nova (Cursor / Agent)."""

from __future__ import annotations

import json
import time
from collections.abc import Iterator
from typing import Any

from fastapi import HTTPException
from fastapi.responses import JSONResponse, StreamingResponse

from nova.openai_cursor_compat import (
    build_chat_completion_response,
    build_responses_api_response,
    extract_user_prompt,
    format_sse_chat_chunk,
    format_sse_done,
    lawful_receipt_header_payload,
    normalize_request,
)
from nova.provider_factory import resolve_provider_model
from nova.runtime_factory import build_lawful_llm, resolve_frontier_provider


def list_openai_models() -> dict[str, Any]:
    now = int(time.time())
    model_ids = (
        "lawful-nova",
        "lawfulnova",
        "nvidia/nemotron-3-ultra-550b-a55b",
    )
    return {
        "object": "list",
        "data": [
            {
                "id": model_id,
                "object": "model",
                "created": now,
                "owned_by": "local-lawful-nova",
            }
            for model_id in model_ids
        ],
    }


def _receipt_chain(receipt: dict[str, Any]) -> dict[str, Any]:
    payload = json.loads(str(receipt["payload"]))
    chain = {
        "identity": payload["identity"],
        "trace": payload["trace"],
        "authority_boundary": payload["authority_boundary"],
        "reproducibility": payload["reproducibility"],
    }
    if "law_kernel" in payload:
        chain["law_kernel"] = payload["law_kernel"]
    return chain


def _receipt_headers(llm: Any, turn: Any) -> dict[str, str]:
    cortex = turn.nova_cortex if hasattr(turn, "nova_cortex") else {}
    frontier_mode = "active" if isinstance(cortex, dict) and cortex.get("provider") else "stub"
    return {
        "X-Lawful-Nova-Frontier": frontier_mode,
        "X-Lawful-Nova-Receipt": lawful_receipt_header_payload(
            turn_receipt=turn.receipt,
            voss_runtime=turn.voss_runtime,
            law_kernel=turn.law_kernel,
            receipt_verified=llm.verify_receipt(turn.receipt),
            chain=_receipt_chain(turn.receipt),
        )
    }


def _stream_chat_completion(
  *,
  normalized: Any,
  llm: Any,
) -> Iterator[str]:
    provider = resolve_frontier_provider()
    frontier_model = resolve_provider_model(normalized.model, provider)
    chunk_id = f"chatcmpl-nova-{int(time.time() * 1000)}"
    if provider is None or not hasattr(provider, "invoke_stream"):
        turn = llm.complete_openai(
            normalized.messages,
            tenant_id=normalized.tenant_id,
            capability=normalized.capability,
            tools=normalized.tools,
            model=normalized.model,
            max_tokens=normalized.max_tokens or normalized.max_completion_tokens,
            temperature=normalized.temperature,
            top_p=normalized.top_p,
        )
        content = str(turn.text or "")
        yield format_sse_chat_chunk(
            chunk_id=chunk_id,
            model=normalized.model,
            delta={"role": "assistant", "content": content},
        )
        yield format_sse_chat_chunk(
            chunk_id=chunk_id,
            model=normalized.model,
            delta={},
            finish_reason="stop",
        )
        yield format_sse_done()
        return

    if hasattr(provider, "iter_stream_sync"):
        sent_role = False
        for upstream in provider.iter_stream_sync(
            normalized.messages,
            tools=normalized.tools,
            model=frontier_model,
            max_tokens=normalized.max_tokens or normalized.max_completion_tokens,
            temperature=normalized.temperature,
            top_p=normalized.top_p,
        ):
            choice = ((upstream.get("choices") or [None])[0]) or {}
            delta = choice.get("delta") or {}
            if not sent_role and not delta.get("role"):
                delta = {**delta, "role": "assistant"}
                sent_role = True
            yield format_sse_chat_chunk(
                chunk_id=chunk_id,
                model=normalized.model,
                delta=delta,
                finish_reason=choice.get("finish_reason"),
            )
        yield format_sse_done()
        return

    import asyncio

    async def _run() -> list[dict[str, Any]]:
        chunks: list[dict[str, Any]] = []
        async for chunk in provider.invoke_stream(
            normalized.messages,
            tools=normalized.tools,
            model=frontier_model,
            max_tokens=normalized.max_tokens or normalized.max_completion_tokens,
            temperature=normalized.temperature,
            top_p=normalized.top_p,
        ):
            chunks.append(chunk)
        return chunks

    upstream_chunks = asyncio.run(_run())
    sent_role = False
    for upstream in upstream_chunks:
        choice = ((upstream.get("choices") or [None])[0]) or {}
        delta = choice.get("delta") or {}
        if not sent_role and not delta.get("role"):
            delta = {**delta, "role": "assistant"}
            sent_role = True
        yield format_sse_chat_chunk(
            chunk_id=chunk_id,
            model=normalized.model,
            delta=delta,
            finish_reason=choice.get("finish_reason"),
        )
    yield format_sse_done()


def handle_openai_completion(body: dict[str, Any]) -> JSONResponse | StreamingResponse:
    normalized = normalize_request(body)
    llm = build_lawful_llm(operator_session_id="nova-local-api", signing_secret="local-api-secret")

    if normalized.stream:
        return StreamingResponse(
            _stream_chat_completion(normalized=normalized, llm=llm),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
        )

    try:
        turn = llm.complete_openai(
            normalized.messages,
            tenant_id=normalized.tenant_id,
            capability=normalized.capability,
            tools=normalized.tools,
            model=normalized.model,
            max_tokens=normalized.max_tokens or normalized.max_completion_tokens,
            temperature=normalized.temperature,
            top_p=normalized.top_p,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    content = str(turn.text or "")
    headers = _receipt_headers(llm, turn)
    if normalized.kind == "responses":
        payload = build_responses_api_response(model=normalized.model, content=content)
    else:
        prompt = extract_user_prompt(normalized.messages)
        payload = build_chat_completion_response(
            model=normalized.model,
            content=content,
            prompt_tokens=max(1, len(prompt.split())),
            completion_tokens=max(1, len(content.split())) if content.strip() else 1,
        )
    return JSONResponse(content=payload, headers=headers)
