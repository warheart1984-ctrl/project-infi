from __future__ import annotations

from typing import Any


def detect(*, artifact: dict[str, Any] | None = None, job: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    meta = (artifact or {}).get("metadata") or {}
    if meta.get("attestation_failed"):
        return [{"organ": "forgekeeper", "severity": 2, "code": "attestation", "violation_class": "II", "message": "attestation hook drift"}]
    return []
