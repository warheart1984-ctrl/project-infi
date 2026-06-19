"""HTTP compatibility surface for the local Lawful Nova slice."""

from __future__ import annotations

import os
import json
from typing import Any

from fastapi import FastAPI
from pydantic import BaseModel, Field

from nova.runtime_factory import build_lawful_llm, collect_runtime_health


class ChatRequest(BaseModel):
    prompt: str = Field(min_length=1)
    tenant_id: str = "local"
    capability: str = "observe"


app = FastAPI(title="Local Lawful Nova API", version="0.1.0")


@app.get("/health")
def health() -> dict[str, Any]:
    return {"status": "ok", "service": "nova_local_api", **collect_runtime_health()}


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
        "receipt": turn.receipt,
        "chain": _receipt_chain(turn.receipt),
        "receipt_verified": llm.verify_receipt(turn.receipt),
    }


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
