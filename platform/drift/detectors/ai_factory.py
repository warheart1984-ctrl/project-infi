from __future__ import annotations

from typing import Any


def detect(*, artifact: dict[str, Any] | None = None, job: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    meta = (artifact or {}).get("metadata") or {}
    if meta.get("proof_manifest_failed"):
        return [
            {
                "organ": "ai_factory",
                "severity": 3,
                "code": "proof_manifest_failed",
                "violation_class": "III",
                "message": "factory proof manifest failure",
            }
        ]
    return []
