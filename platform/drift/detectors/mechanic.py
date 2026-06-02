from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _load_dogfood_scan(case_id: str = "infi-dogfood") -> dict[str, Any] | None:
    scan_path = Path(".runtime/mechanic") / case_id / "mechanic_scan.v1.json"
    if not scan_path.is_file():
        return None
    try:
        return json.loads(scan_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


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

    scan = _load_dogfood_scan()
    if scan:
        drifts = list(scan.get("drifts") or [])
        critical = [d for d in drifts if str(d.get("severity") or "").lower() == "critical"]
        high = [d for d in drifts if str(d.get("severity") or "").lower() == "high"]
        if critical:
            findings.append(
                {
                    "organ": "mechanic",
                    "severity": 3,
                    "code": "DOGFOOD-CRITICAL",
                    "violation_class": "III",
                    "message": f"dogfood scan has {len(critical)} critical drift(s)",
                    "metadata": {"codes": [d.get("code") for d in critical[:5]]},
                }
            )
        elif high:
            findings.append(
                {
                    "organ": "mechanic",
                    "severity": 2,
                    "code": "DOGFOOD-HIGH",
                    "violation_class": "II",
                    "message": f"dogfood scan has {len(high)} high drift(s)",
                    "metadata": {"codes": [d.get("code") for d in high[:5]]},
                }
            )

    job_meta = dict((job or {}).get("metadata") or {})
    result = dict(job_meta.get("result") or {})
    if result.get("launch_blocked"):
        findings.append(
            {
                "organ": "mechanic",
                "severity": 2,
                "code": "MECH-LAUNCH-BLOCKED",
                "violation_class": "II",
                "message": "mechanic/slingshot launch blocked in job result",
            }
        )
    return findings
