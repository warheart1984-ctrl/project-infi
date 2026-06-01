from __future__ import annotations

from typing import Any


def detect(*, artifact: dict[str, Any] | None = None, job: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    if (artifact or {}).get("artifact_type") == "lab_session_receipt":
        meta = (artifact or {}).get("metadata") or {}
        if meta.get("anomaly"):
            return [{"organ": "lab", "severity": 2, "code": "receipt_anomaly", "violation_class": "II", "message": "lab receipt anomaly"}]
    return []
