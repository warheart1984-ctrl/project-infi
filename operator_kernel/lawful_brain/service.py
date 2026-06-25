"""HTTP service for POST /v1/lawful_ask."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from operator_kernel.contracts import LawfulAskRequest, LawfulAskResponse
from operator_kernel.lawful_brain.adapter import LawfulBrainAdapter

app = FastAPI(title="Lawful Brain", version="0.1.0")
_adapter = LawfulBrainAdapter()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "lawful_brain"}


@app.post("/v1/lawful_ask", response_model=LawfulAskResponse)
def lawful_ask(request: LawfulAskRequest) -> LawfulAskResponse:
    return _adapter.ask(request)


def main() -> None:
    import uvicorn

    port = int(__import__("os").environ.get("LAWFUL_BRAIN_PORT", "8791"))
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="info")


if __name__ == "__main__":
    main()
