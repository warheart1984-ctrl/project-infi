from __future__ import annotations

import time
from typing import Any

metrics: dict[str, Any] = {
    "requests": 0,
    "stream_requests": 0,
    "errors": 0,
    "last_request_ts": None,
    "provider": None,
    "model": None,
}


def record_request(provider: str, model: str, *, stream: bool = False) -> None:
    metrics["requests"] += 1
    if stream:
        metrics["stream_requests"] += 1
    metrics["last_request_ts"] = int(time.time())
    metrics["provider"] = provider
    metrics["model"] = model


def record_error() -> None:
    metrics["errors"] += 1
