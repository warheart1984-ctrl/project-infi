from __future__ import annotations

from typing import Any


def detect(*, artifact: dict[str, Any] | None = None, job: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    meta = (artifact or {}).get("metadata") or {}
    if meta.get("drift_detected") or meta.get("health_drift"):
        findings.append(
            {
                "organ": "mechanic",
                "severity": 2,
                "code": "health_drift",
                "violation_class": "II",
                "message": "mechanic health drift index anomaly",
            }
        )
    if (job or {}).get("kind") == "mechanic.scan" and (job or {}).get("status") == "failed":
        findings.append({"organ": "mechanic", "severity": 1, "code": "scan_failed", "message": "scan failed"})
    return findings
