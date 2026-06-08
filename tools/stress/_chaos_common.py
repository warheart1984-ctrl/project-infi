"""Shared chaos stress helpers for operator hammer scripts."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

BASE = os.environ.get("AAIS_STRESS_BASE", "http://127.0.0.1:8000")
LEGACY = f"{BASE}/legacy_api"
TIMEOUT = 20


def configure_base(base: str) -> None:
    """Override stress target base URL (also updates LEGACY prefix)."""
    global BASE, LEGACY
    BASE = base.rstrip("/")
    LEGACY = f"{BASE}/legacy_api"


@dataclass
class ChaosResult:
    name: str
    status: int | None
    ok: bool
    note: str = ""
    expected_fail: bool = False


@dataclass
class ChaosReport:
    results: list[ChaosResult] = field(default_factory=list)
    unexpected_failures: list[ChaosResult] = field(default_factory=list)
    server_errors: list[ChaosResult] = field(default_factory=list)

    def add(self, r: ChaosResult) -> None:
        self.results.append(r)
        if r.status is not None and r.status >= 500:
            self.server_errors.append(r)
        elif not r.ok and not r.expected_fail:
            self.unexpected_failures.append(r)


def _req(
    method: str,
    path: str,
    *,
    body: bytes | None = None,
    headers: dict | None = None,
    legacy: bool = False,
    fastapi: bool = False,
) -> tuple[int | None, str]:
    if fastapi or path.startswith("/api/ugr/"):
        base = BASE
    elif legacy or path.startswith("/api/"):
        base = LEGACY
    else:
        base = BASE
    url = f"{base}{path}"
    hdrs = dict(headers or {})
    if body is not None and "Content-Type" not in hdrs:
        hdrs["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=body, headers=hdrs, method=method)
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            return resp.status, (resp.read() or b"").decode("utf-8", errors="replace")[:500]
    except urllib.error.HTTPError as e:
        body_text = (e.read() or b"").decode("utf-8", errors="replace")[:500]
        return e.code, body_text
    except Exception as e:
        return None, str(e)[:300]


def _json_post(path: str, payload: dict | list | str, *, legacy: bool = True) -> ChaosResult:
    if isinstance(payload, str):
        body = payload.encode("utf-8")
    else:
        body = json.dumps(payload).encode("utf-8")
    status, text = _req("POST", path, body=body, legacy=legacy)
    ok = status is not None and status < 500
    return ChaosResult(name=f"POST {path}", status=status, ok=ok, note=text[:120])


def check_health() -> tuple[int | None, str]:
    return _req("GET", "/health")


def server_reachable() -> bool:
    status, _ = check_health()
    return status == 200


def write_chaos_report(
    report: ChaosReport,
    summary: dict,
    *,
    filename: str,
) -> Path:
    out = ROOT / "ci-artifacts" / filename
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "summary": summary,
        "server_errors": [r.__dict__ for r in report.server_errors],
        "unexpected_failures": [r.__dict__ for r in report.unexpected_failures],
        "all_results_count": len(report.results),
    }
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return out
