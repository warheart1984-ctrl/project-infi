#!/usr/bin/env python
"""
Seam discovery stress harness — auto-discover runtime seams under live pressure.

Harvests Flask routes, cross-references subsystem genomes, probes live surfaces,
classifies failures per SEAM_LAW, logs to seam-events.jsonl, and writes reports.

Run while AAIS is live:
  python -m aais start --data-dir ./.runtime/aais-data --preset mock --no-browser
  python tools/stress/seam_discovery_stress.py

Offline route harvest only (no live server):
  python tools/stress/seam_discovery_stress.py --offline
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass, field
from datetime import date
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    import requests
except ImportError:
    requests = None  # type: ignore[assignment]

BASE = os.environ.get("AAIS_STRESS_BASE", "http://127.0.0.1:8000")
LEGACY = f"{BASE}/legacy_api"
TIMEOUT = int(os.environ.get("AAIS_SEAM_TIMEOUT", "15"))
SLOW_ROUTE_TIMEOUT = int(os.environ.get("AAIS_SEAM_SLOW_TIMEOUT", "45"))
CONCURRENCY = int(os.environ.get("AAIS_SEAM_CONC", "8"))
SLOW_ROUTE_PREFIXES = (
    "/api/operator/console",
    "/api/operator/console/mesh-health",
)
GENOME_DIR = ROOT / "governance" / "subsystem_genomes"
ARTIFACT_DIR = ROOT / "ci-artifacts"
AUDIT_DIR = ROOT / "docs" / "audit"
SEAM_RECORDS_DIR = ROOT / "docs" / "contracts" / "seams"

# Safe path-parameter substitutions for smoke probes.
_PARAM_DEFAULTS: dict[str, str] = {
    "session_id": "global",
    "subject_type": "operator_session",
    "subject_id": "global",
    "grant_id": "smoke-grant",
    "plug_id": "smoke-plug",
    "workflow_id": "smoke-workflow",
    "run_id": "smoke-run",
    "workflow_family_id": "smoke-family",
    "organ_id": "smoke-organ",
    "pipeline_id": "smoke-pipeline",
    "mission_id": "smoke-mission",
    "case_id": "smoke-case",
    "pack_id": "smoke-pack",
    "pattern_id": "smoke-pattern",
    "extraction_id": "smoke-extraction",
    "id": "smoke-id",
}

OPERATOR_PROBE_PATHS = [
    "/api/operator/ledger",
    "/api/operator/ledger/digest",
    "/api/operator/ledger/query",
    "/api/operator/plugins",
    "/api/operator/plugins/libraries",
    "/api/operator/plugins/workflows",
    "/api/operator/organs",
    "/api/operator/brain",
    "/api/operator/brain/sessions",
    "/api/operator/replay/operator_session/global/timeline",
    "/api/jarvis/operator-decision-ledger/status",
]

SHELL_PROBE_PATHS = [
    "/health",
    "/health/details",
    "/workflows/templates",
    "/workflows/approvals",
]

HIGH_VALUE_JARVIS_PATHS = [
    "/api/jarvis/capability-bridge",
    "/api/jarvis/capability-bridge/status",
    "/api/jarvis/memory/board",
    "/api/jarvis/providers",
]


@dataclass
class RouteSpec:
    rule: str
    methods: list[str]
    surface: str = "legacy"

    @property
    def probe_path(self) -> str:
        path = self.rule
        for match in re.finditer(r"<(?:[^:>]+:)?([^>]+)>", path):
            key = match.group(1)
            path = path.replace(match.group(0), _PARAM_DEFAULTS.get(key, f"smoke-{key}"), 1)
        return path

    @property
    def primary_method(self) -> str:
        methods = [m for m in self.methods if m not in {"HEAD", "OPTIONS"}]
        if "GET" in methods:
            return "GET"
        if "POST" in methods:
            return "POST"
        return methods[0] if methods else "GET"


@dataclass
class ProbeResult:
    path: str
    method: str
    status: int | None = None
    latency_ms: float = 0.0
    error: str | None = None
    body_len: int = 0
    genome_gene: str | None = None
    seam_class: str | None = None
    severity: str | None = None
    boundary: str | None = None
    law: str | None = None
    failure: bool = False
    closure_status: str = "open"


@dataclass
class DiscoveryReport:
    generated_at: str
    base: str
    offline: bool
    route_inventory: dict[str, Any] = field(default_factory=dict)
    genome_surfaces: list[dict[str, str]] = field(default_factory=list)
    gaps: dict[str, list[str]] = field(default_factory=dict)
    probes: list[dict[str, Any]] = field(default_factory=list)
    failures: list[dict[str, Any]] = field(default_factory=list)
    summary: dict[str, Any] = field(default_factory=dict)
    health: dict[str, Any] = field(default_factory=dict)
    chat_pressure: dict[str, Any] = field(default_factory=dict)


def harvest_flask_routes() -> list[RouteSpec]:
    from src.api import app

    routes: list[RouteSpec] = []
    seen: set[tuple[str, str]] = set()
    for rule in app.url_map.iter_rules():
        methods = sorted(m for m in (rule.methods or set()) if m not in {"HEAD", "OPTIONS"})
        if not methods:
            continue
        key = (rule.rule, ",".join(methods))
        if key in seen:
            continue
        seen.add(key)
        routes.append(RouteSpec(rule=rule.rule, methods=methods))
    return sorted(routes, key=lambda r: (r.rule, r.primary_method))


def harvest_genome_api_surfaces() -> list[dict[str, str]]:
    surfaces: list[dict[str, str]] = []
    for path in sorted(GENOME_DIR.glob("*.genome.v1.json")):
        try:
            genome = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        gene = (genome.get("identity") or {}).get("gene") or path.stem
        for entry in (genome.get("runtime") or {}).get("surface") or []:
            if str(entry.get("kind") or "").lower() != "api":
                continue
            api_path = str(entry.get("path") or "").strip()
            if not api_path:
                continue
            surfaces.append({"gene": gene, "path": api_path, "genome_file": path.name})
    return surfaces


def _normalize_genome_path(api_path: str) -> tuple[str, str]:
    """Return (method, flask_rule_path) from genome api surface string."""
    parts = api_path.split(None, 1)
    if len(parts) == 2 and parts[0].upper() in {"GET", "POST", "PUT", "PATCH", "DELETE"}:
        method, path = parts[0].upper(), parts[1].strip()
    else:
        method, path = "GET", api_path.strip()
    if not path.startswith("/"):
        path = "/" + path
    return method, path


def _normalize_route_pattern(path: str) -> str:
    """Normalize Flask/genome path patterns for comparison."""
    normalized = path.strip()
    if not normalized.startswith("/"):
        normalized = "/" + normalized
    return re.sub(r"\{([^}]+)\}", r"<\1>", normalized)


def _route_has_params(rule: str) -> bool:
    return "<" in rule or "{" in rule


def compute_gaps(
    routes: list[RouteSpec],
    genome_surfaces: list[dict[str, str]],
    stress_paths: set[str] | None = None,
) -> dict[str, list[str]]:
    flask_rules = {_normalize_route_pattern(r.rule) for r in routes}
    jarvis_status = sorted(
        r.rule for r in routes if "/api/jarvis/" in r.rule and r.rule.endswith("/status")
    )
    operator_rules = sorted(r.rule for r in routes if "/api/operator/" in r.rule)

    genome_missing: list[str] = []
    for surface in genome_surfaces:
        method, path = _normalize_genome_path(surface["path"])
        if _normalize_route_pattern(path) not in flask_rules:
            genome_missing.append(f"{method} {path} ({surface['gene']})")

    stress_missing: list[str] = []
    if stress_paths is not None:
        for path in sorted(stress_paths):
            if path not in flask_rules:
                stress_missing.append(path)

    return {
        "genome_declared_missing_from_flask": genome_missing,
        "jarvis_status_routes": jarvis_status,
        "operator_routes": operator_rules,
        "stress_list_missing_from_flask": stress_missing,
    }


def _classify_failure(
    *,
    path: str,
    method: str,
    status: int | None,
    error: str | None,
    genome_gene: str | None,
    rule: str | None = None,
    health_degraded: bool = False,
) -> tuple[bool, str, str, str, str]:
    """Return failure, seam_class, severity, boundary, law."""
    if error:
        if "refused" in error.lower() or "timeout" in error.lower():
            return (
                True,
                "tool_invocation_seam",
                "critical",
                "live_server_connectivity",
                "Live stress probes must reach the AAIS server without connection failure.",
            )
        return (
            True,
            "tool_invocation_seam",
            "high",
            "http_probe",
            f"HTTP probe must complete for {path}.",
        )

    if health_degraded and path in {"/health", "/health/details"}:
        return (
            True,
            "routing_seam",
            "critical",
            "health_surface",
            "Health endpoint must report healthy with legacy bridge mounted.",
        )

    if status is not None and status >= 500:
        boundary = "jarvis_status_farm" if "/status" in path else "runtime_api"
        return (
            True,
            "governance_seam",
            "critical",
            boundary,
            f"Runtime surface {method} {path} must not return 5xx under smoke probe.",
        )

    if status == 404 and genome_gene:
        return (
            True,
            "governance_seam",
            "high",
            "genome_runtime_surface",
            f"Genome-declared surface for {genome_gene} must be registered in Flask url_map.",
        )

    if status == 404 and path.startswith("/api/operator/") and not _route_has_params(rule or path):
        return (
            True,
            "governance_seam",
            "high",
            "operator_product_surface",
            "Operator API routes must be registered and reachable via legacy bridge.",
        )

    if status == 404 and path.endswith("/status") and "/api/jarvis/" in path:
        return (
            True,
            "governance_seam",
            "medium",
            "jarvis_status_farm",
            "Jarvis status routes declared in stress inventory must return 200 smoke responses.",
        )

    return False, "", "", "", ""


def _probe_url(path: str, method: str) -> str:
    if path.startswith("/api/"):
        return f"{LEGACY}{path}"
    return f"{BASE}{path}"


def probe_route(spec: RouteSpec, genome_gene: str | None = None) -> ProbeResult:
    path = spec.probe_path
    method = spec.primary_method
    url = _probe_url(path, method)
    start = time.time()
    status: int | None = None
    error: str | None = None
    body_len = 0
    timeout = SLOW_ROUTE_TIMEOUT if any(path.startswith(prefix) for prefix in SLOW_ROUTE_PREFIXES) else TIMEOUT

    if requests is None:
        error = "requests package unavailable"
    else:
        try:
            if method == "GET":
                resp = requests.get(url, timeout=timeout)
            else:
                resp = requests.post(url, json={}, timeout=timeout)
            status = resp.status_code
            body_len = len(resp.text or "")
        except Exception as exc:
            error = str(exc)[:200]

    latency_ms = round((time.time() - start) * 1000, 1)
    failure, seam_class, severity, boundary, law = _classify_failure(
        path=path,
        method=method,
        status=status,
        error=error,
        genome_gene=genome_gene,
        rule=spec.rule,
    )
    return ProbeResult(
        path=path,
        method=method,
        status=status,
        latency_ms=latency_ms,
        error=error,
        body_len=body_len,
        genome_gene=genome_gene,
        seam_class=seam_class or None,
        severity=severity or None,
        boundary=boundary or None,
        law=law or None,
        failure=failure,
    )


def probe_health() -> dict[str, Any]:
    if requests is None:
        return {"reachable": False, "error": "requests unavailable"}
    try:
        resp = requests.get(f"{BASE}/health", timeout=TIMEOUT)
        body = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {}
        legacy_error = body.get("legacy_api_mount_error")
        return {
            "reachable": True,
            "status_code": resp.status_code,
            "healthy": body.get("status") == "healthy" and resp.status_code == 200,
            "legacy_api_loaded": body.get("legacy_api_loaded"),
            "legacy_api_mount_error": legacy_error,
            "degraded": body.get("status") != "healthy" or bool(legacy_error),
        }
    except Exception as exc:
        return {"reachable": False, "error": str(exc)[:200]}


def run_chat_pressure() -> dict[str, Any]:
    """Three identical turns + one long turn — identity and budget seams."""
    if requests is None:
        return {"skipped": True, "reason": "requests unavailable"}

    result: dict[str, Any] = {"identity_stable": True, "turns": []}
    try:
        sess_resp = requests.post(
            f"{LEGACY}/api/chat/sessions",
            json={"system_prompt": "Stress seam discovery. Reply in one short sentence."},
            timeout=TIMEOUT,
        )
        if sess_resp.status_code >= 300:
            result["session_error"] = sess_resp.status_code
            return result
        session_id = (sess_resp.json() or {}).get("session_id")
        if not session_id:
            result["session_error"] = "missing session_id"
            return result

        identical_msg = "Report subsystem readiness in exactly five words."
        replies: list[str] = []
        for i in range(3):
            msg_resp = requests.post(
                f"{LEGACY}/api/chat/sessions/{session_id}/message",
                json={"message": identical_msg, "response_mode": "operator"},
                timeout=TIMEOUT,
            )
            body = msg_resp.json() if msg_resp.headers.get("content-type", "").startswith("application/json") else {}
            reply = str(body.get("reply") or body.get("message") or body.get("content") or "")[:500]
            replies.append(reply)
            result["turns"].append({"turn": i + 1, "status": msg_resp.status_code, "reply_len": len(reply)})

        if len({r.strip().lower() for r in replies if r}) > 1:
            result["identity_stable"] = False
            result["identity_seam"] = "replies diverged on identical input"

        long_msg = " ".join(["Summarize every governed subsystem boundary."] * 80)
        long_resp = requests.post(
            f"{LEGACY}/api/chat/sessions/{session_id}/message",
            json={"message": long_msg, "response_mode": "operator"},
            timeout=TIMEOUT * 2,
        )
        long_body = long_resp.json() if long_resp.headers.get("content-type", "").startswith("application/json") else {}
        long_reply = str(long_body.get("reply") or long_body.get("message") or "")
        result["long_turn"] = {
            "status": long_resp.status_code,
            "reply_len": len(long_reply),
            "truncated_suspected": long_resp.status_code >= 500 or (0 < len(long_reply) < 20),
        }
    except Exception as exc:
        result["error"] = str(exc)[:200]
    return result


def _genome_lookup(genome_surfaces: list[dict[str, str]]) -> dict[str, str]:
    lookup: dict[str, str] = {}
    for surface in genome_surfaces:
        _method, path = _normalize_genome_path(surface["path"])
        lookup[path] = surface["gene"]
    return lookup


def select_probe_specs(routes: list[RouteSpec]) -> list[RouteSpec]:
    """Choose smoke-safe routes: status farm, operator, shell, high-value jarvis."""
    selected: dict[str, RouteSpec] = {}
    for spec in routes:
        rule = spec.rule
        if rule.endswith("/status") and "/api/jarvis/" in rule:
            selected[rule] = spec
        elif "/api/operator/" in rule and spec.primary_method == "GET":
            selected[rule] = spec
        elif rule in SHELL_PROBE_PATHS or rule in HIGH_VALUE_JARVIS_PATHS:
            selected[rule] = spec

    for path in OPERATOR_PROBE_PATHS + SHELL_PROBE_PATHS + HIGH_VALUE_JARVIS_PATHS:
        for spec in routes:
            if spec.rule == path or spec.probe_path == path:
                selected[spec.rule] = spec

    return sorted(selected.values(), key=lambda s: s.rule)


def log_seam_failures(failures: list[ProbeResult], *, runtime_dir: str | None = None) -> list[dict[str, Any]]:
    from src.seam_log import record_seam_event

    logged: list[dict[str, Any]] = []
    for item in failures:
        if not item.failure:
            continue
        event = record_seam_event(
            classification="boundary_violation",
            source="seam_discovery_stress",
            boundary=item.boundary or "runtime_boundary",
            reason=item.law or item.error or f"probe failure {item.path}",
            severity=item.severity or "medium",
            event_type=item.seam_class or "governance_seam",
            runtime_context="operator_runtime",
            details={
                "path": item.path,
                "method": item.method,
                "status": item.status,
                "latency_ms": item.latency_ms,
                "genome_gene": item.genome_gene,
                "error": item.error,
            },
            runtime_dir=runtime_dir or os.environ.get("AAIS_RUNTIME_DIR"),
        )
        logged.append(event)
    return logged


def write_seam_live_record(failure: ProbeResult, record_id: str) -> Path:
    SEAM_RECORDS_DIR.mkdir(parents=True, exist_ok=True)
    short = re.sub(r"[^a-z0-9]+", "-", failure.path.strip("/").lower())[:40].strip("-")
    filename = f"SEAM-LIVE-{record_id}-{short}.md"
    path = SEAM_RECORDS_DIR / filename
    content = f"""# {record_id}

## Title

Live probe failure: `{failure.method} {failure.path}`

## Classification

- seam class: `{failure.seam_class or "governance_seam"}`
- boundary: `{failure.boundary or "runtime_boundary"}`
- severity: `{failure.severity or "medium"}`
- status: open
- discovery state: reproduced under seam_discovery_stress live probe

## Summary

Live seam discovery recorded a boundary violation during operator-mode stress.

## Detection Capture

- endpoint: `{failure.method} {failure.path}`
- status code: `{failure.status}`
- latency_ms: `{failure.latency_ms}`
- error: `{failure.error or "none"}`

## Law Definition

{failure.law or "Runtime surface must respond without 5xx or missing registration under smoke probe."}

## Closure

- [ ] Fix registered route or handler
- [ ] Regression test added
- [ ] Re-run seam_discovery_stress.py — probe green
"""
    path.write_text(content, encoding="utf-8")
    return path


def write_audit_rollup(report: DiscoveryReport, seam_record_paths: list[str]) -> Path:
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    run_date = date.today().isoformat()
    out = AUDIT_DIR / f"SEAM_STRESS_RUN_{run_date}.md"
    failures = report.failures
    lines = [
        f"# Seam Stress Run — {run_date}",
        "",
        "## Operator summary",
        "",
        f"- Base: `{report.base}`",
        f"- Offline harvest: `{report.offline}`",
        f"- Total probes: `{report.summary.get('total_probes', 0)}`",
        f"- Failures: `{report.summary.get('failure_count', 0)}`",
        f"- Critical/high: `{report.summary.get('critical_high_count', 0)}`",
        "",
        "## Health",
        "",
        f"```json\n{json.dumps(report.health, indent=2)}\n```",
        "",
        "## Findings",
        "",
        "| Endpoint | Status | Severity | Seam class | Closure |",
        "|----------|--------|----------|------------|---------|",
    ]
    if failures:
        for f in failures:
            lines.append(
                f"| `{f.get('method')} {f.get('path')}` | {f.get('status')} | "
                f"{f.get('severity')} | {f.get('seam_class')} | open |"
            )
    else:
        lines.append("| _none_ | — | — | — | closed |")

    lines.extend(
        [
            "",
            "## Genome gaps (declared API missing from Flask)",
            "",
        ]
    )
    gaps = report.gaps.get("genome_declared_missing_from_flask") or []
    if gaps:
        for gap in gaps[:30]:
            lines.append(f"- {gap}")
        if len(gaps) > 30:
            lines.append(f"- ... and {len(gaps) - 30} more")
    else:
        lines.append("- none")

    lines.extend(["", "## Seam records", ""])
    if seam_record_paths:
        for p in seam_record_paths:
            lines.append(f"- `{p}`")
    else:
        lines.append("- none (clean run)")

    lines.extend(["", "## Chat pressure", "", f"```json\n{json.dumps(report.chat_pressure, indent=2)}\n```", ""])
    out.write_text("\n".join(lines), encoding="utf-8")
    return out


def run_discovery(*, offline: bool = False, log_seams: bool = True, write_records: bool = True) -> DiscoveryReport:
    routes = harvest_flask_routes()
    genome_surfaces = harvest_genome_api_surfaces()
    genome_by_path = _genome_lookup(genome_surfaces)

    try:
        from tools.stress.live_api_stress import SUBSYSTEM_STATUSES
    except ImportError:
        SUBSYSTEM_STATUSES = []

    gaps = compute_gaps(routes, genome_surfaces, stress_paths=set(SUBSYSTEM_STATUSES))
    inventory = {
        "total_routes": len(routes),
        "jarvis_routes": sum(1 for r in routes if "/api/jarvis/" in r.rule),
        "operator_routes": sum(1 for r in routes if "/api/operator/" in r.rule),
        "jarvis_status_routes": sum(1 for r in routes if r.rule.endswith("/status") and "/api/jarvis/" in r.rule),
    }

    report = DiscoveryReport(
        generated_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        base=BASE,
        offline=offline,
        route_inventory=inventory,
        genome_surfaces=genome_surfaces,
        gaps=gaps,
    )

    health = probe_health() if not offline else {"skipped": True}
    report.health = health

    chat_pressure: dict[str, Any] = {}
    probe_results: list[ProbeResult] = []

    if offline:
        report.summary = {
            "total_probes": 0,
            "failure_count": 0,
            "critical_high_count": 0,
            "mode": "offline_harvest",
        }
    else:
        specs = select_probe_specs(routes)
        with ThreadPoolExecutor(max_workers=CONCURRENCY) as pool:
            futures = {
                pool.submit(probe_route, spec, genome_by_path.get(spec.rule)): spec for spec in specs
            }
            for fut in as_completed(futures):
                probe_results.append(fut.result())

        if health.get("degraded"):
            probe_results.append(
                ProbeResult(
                    path="/health",
                    method="GET",
                    status=health.get("status_code"),
                    failure=True,
                    seam_class="routing_seam",
                    severity="critical",
                    boundary="health_surface",
                    law="Health endpoint must report healthy with legacy bridge mounted.",
                )
            )

        chat_pressure = run_chat_pressure()
        report.chat_pressure = chat_pressure
        if not chat_pressure.get("identity_stable", True):
            probe_results.append(
                ProbeResult(
                    path="/api/chat/sessions/*/message",
                    method="POST",
                    status=200,
                    failure=True,
                    seam_class="identity_seam",
                    severity="high",
                    boundary="chat_identity",
                    law="Identical operator turns must produce stable semantic identity.",
                )
            )
        if chat_pressure.get("long_turn", {}).get("truncated_suspected"):
            probe_results.append(
                ProbeResult(
                    path="/api/chat/sessions/*/message",
                    method="POST",
                    status=chat_pressure.get("long_turn", {}).get("status"),
                    failure=True,
                    seam_class="context_window_seam",
                    severity="medium",
                    boundary="chat_output_budget",
                    law="Long-turn operator chat must not silently collapse output budget.",
                )
            )

    failures = [p for p in probe_results if p.failure]
    report.probes = [asdict(p) for p in probe_results]
    report.failures = [asdict(p) for p in failures]
    summary = {
        "total_probes": len(probe_results),
        "failure_count": len(failures),
        "critical_high_count": sum(1 for p in failures if p.severity in {"critical", "high"}),
        "ok_count": len(probe_results) - len(failures),
    }
    if offline:
        summary["mode"] = "offline_harvest"
    report.summary = summary

    if log_seams and failures and not offline:
        log_seam_failures(failures)

    seam_record_paths: list[str] = []
    if write_records and failures and not offline:
        for idx, failure in enumerate(failures, start=1):
            record_id = f"{idx:03d}"
            rec_path = write_seam_live_record(failure, record_id)
            seam_record_paths.append(str(rec_path.relative_to(ROOT)))

    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    artifact_path = ARTIFACT_DIR / "seam_discovery_report.json"
    artifact_path.write_text(json.dumps(asdict(report), indent=2), encoding="utf-8")

    if not offline:
        audit_path = write_audit_rollup(report, seam_record_paths)
        print(f"Audit rollup: {audit_path}")

    print(f"Discovery report: {artifact_path}")
    print(
        f"Probes={report.summary.get('total_probes')} failures={report.summary.get('failure_count')} "
        f"critical/high={report.summary.get('critical_high_count')}"
    )
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="AAIS seam discovery stress harness")
    parser.add_argument("--offline", action="store_true", help="Route/genome harvest only; no live probes")
    parser.add_argument("--no-log", action="store_true", help="Skip seam-events.jsonl logging")
    parser.add_argument("--no-records", action="store_true", help="Skip SEAM-LIVE-* markdown records")
    args = parser.parse_args()

    if not args.offline and requests is None:
        print("ERROR: requests required for live probes. pip install requests or use --offline.")
        return 2

    report = run_discovery(
        offline=args.offline,
        log_seams=not args.no_log,
        write_records=not args.no_records,
    )
    failure_count = int(report.summary.get("failure_count") or 0)
    return 1 if failure_count else 0


if __name__ == "__main__":
    raise SystemExit(main())
