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
    json_body: dict | list | None = None,
    headers: dict | None = None,
    legacy: bool = False,
    fastapi: bool = False,
    max_body: int = 500,
    timeout: float | None = None,
    parse_json: bool = False,
) -> tuple[int | None, str | object]:
    if json_body is not None:
        body = json.dumps(json_body).encode("utf-8")
        hdrs = dict(headers or {})
        hdrs.setdefault("Content-Type", "application/json")
        headers = hdrs
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
    use_timeout = TIMEOUT if timeout is None else timeout
    try:
        with urllib.request.urlopen(req, timeout=use_timeout) as resp:
            raw = (resp.read() or b"").decode("utf-8", errors="replace")
            if max_body > 0:
                raw = raw[:max_body]
            if parse_json and raw.strip():
                try:
                    return resp.status, json.loads(raw)
                except json.JSONDecodeError:
                    pass
            return resp.status, raw
    except urllib.error.HTTPError as e:
        body_text = (e.read() or b"").decode("utf-8", errors="replace")
        if max_body > 0:
            body_text = body_text[:max_body]
        if parse_json and body_text.strip():
            try:
                return e.code, json.loads(body_text)
            except json.JSONDecodeError:
                pass
        return e.code, body_text
    except Exception as e:
        return None, str(e)[:300]


def check_health(base_url: str | None = None) -> tuple[int | None, str | object]:
    if base_url:
        configure_base(base_url)
    return _req("GET", "/health", max_body=2000, parse_json=True)


def _json_post(path: str, payload: dict | list | str, *, legacy: bool = True) -> ChaosResult:
    if isinstance(payload, str):
        body = payload.encode("utf-8")
    else:
        body = json.dumps(payload).encode("utf-8")
    status, text = _req("POST", path, body=body, legacy=legacy)
    ok = status is not None and status < 500
    note = text if isinstance(text, str) else json.dumps(text)[:120]
    return ChaosResult(name=f"POST {path}", status=status, ok=ok, note=note[:120])


def server_reachable() -> bool:
    status, _ = check_health()
    return status == 200


def load_configured_mesh_peers(root: Path | None = None) -> list[str]:
    """Peer URLs from deploy/mesh/peers.json or peers.example.json."""
    root = root or ROOT
    peers_file = root / "deploy" / "mesh" / "peers.json"
    if not peers_file.exists():
        peers_file = root / "deploy" / "mesh" / "peers.example.json"
    if not peers_file.exists():
        return []
    data = json.loads(peers_file.read_text(encoding="utf-8"))
    urls: list[str] = []
    for raw in list(data.get("peers") or []):
        if isinstance(raw, str):
            urls.append(raw.rstrip("/"))
        elif isinstance(raw, dict) and raw.get("url"):
            urls.append(str(raw["url"]).rstrip("/"))
    return urls


def probe_mesh_peers(
    urls: list[str] | None = None,
    *,
    timeout: float = 2.0,
    root: Path | None = None,
) -> dict:
    """Check mesh peer /api/mesh/health before federation-heavy probes."""
    urls = urls if urls is not None else load_configured_mesh_peers(root=root)
    peers: list[dict] = []
    unreachable: list[str] = []
    for url in urls:
        req_url = f"{url}/api/mesh/health"
        req = urllib.request.Request(req_url, method="GET")
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                ok = resp.status == 200
                status = resp.status
        except urllib.error.HTTPError as e:
            ok = False
            status = e.code
        except Exception:
            ok = False
            status = None
        peers.append({"url": url, "ok": ok, "status": status})
        if not ok:
            unreachable.append(url)
    return {
        "ready": len(urls) > 0 and not unreachable,
        "configured": len(urls),
        "peers": peers,
        "unreachable": unreachable,
    }


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
