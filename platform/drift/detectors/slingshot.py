from __future__ import annotations

from typing import Any


def detect(*, artifact: dict[str, Any] | None = None, job: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    meta = (artifact or {}).get("metadata") or (job or {}).get("metadata") or {}
    if meta.get("launch_blocked"):
        findings.append(
            {
                "organ": "slingshot",
                "severity": 3,
                "code": "launch_blocked",
                "violation_class": "III",
                "message": "slingshot launch blocked",
            }
        )
    if str(meta.get("impact_status") or "") in {"blocked", "critical"}:
        findings.append({"organ": "slingshot", "severity": 2, "code": "impact", "violation_class": "II", "message": "impact drift"})
    return findings
