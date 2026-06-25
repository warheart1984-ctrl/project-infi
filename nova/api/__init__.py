"""HTTP compatibility surface for the local Lawful Nova slice."""

from __future__ import annotations

import json
import os
import time
from typing import Any

from fastapi import FastAPI, Request
from pydantic import BaseModel, Field

from nova.api.openai_handlers import handle_openai_completion, list_openai_models
from nova.runtime_factory import build_lawful_llm, collect_runtime_health


class ChatRequest(BaseModel):
    prompt: str = Field(min_length=1)
    tenant_id: str = "local"
    capability: str = "observe"


app = FastAPI(title="Local Lawful Nova API", version="0.1.0")


@app.on_event("startup")
def _constitutional_boot() -> None:
    from governance_gate import require_constitutional_boot

    require_constitutional_boot()


def _register_cockpit_routes() -> None:
    """Register cockpit routes when the dependency graph is healthy."""
    try:
        from nova.api.cockpit import router as cockpit_router

        app.include_router(cockpit_router)
    except ImportError:
        # Cursor/OpenAI compatibility routes must start even if cockpit deps cycle.
        pass


_register_cockpit_routes()


@app.get("/health")
def health() -> dict[str, Any]:
    return {"status": "ok", "service": "nova_local_api", **collect_runtime_health()}


@app.get("/v1/models")
def models() -> dict[str, Any]:
    return list_openai_models()


@app.post("/v1/chat")
def chat(request: ChatRequest) -> dict[str, Any]:
    llm = build_lawful_llm(operator_session_id="nova-local-api", signing_secret="local-api-secret")
    turn = llm.ask(
        request.prompt,
        tenant_id=request.tenant_id,
        capability=request.capability,
    )
    return {
        "text": turn.text,
        "decision": turn.voss_runtime["decision"],
        "law_kernel": turn.law_kernel,
        "receipt": turn.receipt,
        "chain": _receipt_chain(turn.receipt),
        "receipt_verified": llm.verify_receipt(turn.receipt),
    }


@app.post("/v1/chat/completions")
async def chat_completions(request: Request):
    body = await request.json()
    if not isinstance(body, dict):
        body = {}
    return handle_openai_completion(body)


@app.post("/v1/responses")
async def responses_api(request: Request):
    body = await request.json()
    if not isinstance(body, dict):
        body = {}
    return handle_openai_completion(body)


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


def main() -> None:
    import uvicorn

    from governance_gate import require_constitutional_boot

    require_constitutional_boot()
    port = int(os.environ.get("NOVA_PORT", "8080"))
    uvicorn.run("nova.api:app", host="127.0.0.1", port=port, log_level="info")


if __name__ == "__main__":
    main()
