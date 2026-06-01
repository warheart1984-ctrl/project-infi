"""Proof runner registry (v27)."""

from __future__ import annotations

import os
from datetime import datetime
from typing import Any

from src.datetime_compat import UTC

from platform.store import PlatformStore


def enroll_runner(
    *,
    store: PlatformStore,
    runner_id: str,
    region: str = "us",
    public_key_ref: str = "",
    public_key_pem: str = "",
) -> dict[str, Any]:
    payload = {
        "runner_id": runner_id,
        "region": region,
        "public_key_ref": public_key_ref,
        "public_key_pem": public_key_pem,
        "enrolled_at": datetime.now(UTC).isoformat(),
        "status": "active",
    }
    return store.upsert_proof_runner(payload)


def is_runner_enrolled(*, store: PlatformStore, runner_id: str) -> bool:
    if os.environ.get("PLATFORM_ENFORCE_RUNNER_REGISTRY", "0") != "1":
        return True
    rec = store.get_proof_runner(runner_id)
    return rec is not None and rec.get("status") == "active"
