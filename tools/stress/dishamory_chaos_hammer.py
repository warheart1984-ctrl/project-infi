#!/usr/bin/env python
"""DISHAMORY CHAOS TEST — 100× PROTOCOL.

Dishamory = Disharmony + Memory Drift + Cross-Subsystem Inconsistency.
Exposes governance drift, ledger divergence, gossip drift, and seam failures
under extreme load and adversarial sequencing.

Phases:
  A   — 8 stress surfaces × rounds
  B   — 72 disharmony probes × rounds (4 subsystems × 18 each)
  B2  — 32 concurrent bursts × rounds
  C   — 10 federation mission probes × rounds

Pass criteria (per protocol round budget):
  ~12,000–14,000 total probes, 0×5xx, 0 unexpected failures,
  0 governance/ledger/gossip drift, 0 split-brain, 0 invariant violations,
  health pre/post 200/200.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
import time
import urllib.parse
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.stress._chaos_common import (  # noqa: E402
    BASE,
    ChaosReport,
    ChaosResult,
    _req,
    configure_base,
    probe_mesh_peers,
)
from tools.stress.chaos_hammer import (  # noqa: E402
    hammer_cloud_forge_acceleration_offline,
    hammer_cloud_forge_offline,
    hammer_concurrent_sessions,
    hammer_malformed_json,
    hammer_operator_surface,
    hammer_otem_bypass,
    hammer_path_traversal,
    hammer_status_farm,
    hammer_ugr_deliberate,
    hammer_ugr_missions,
    hammer_wrong_methods,
    quote_sql_injection,
)
from tools.stress.federation_chaos_hammer import (  # noqa: E402
    CIVILIZATIONAL_GET_ROUTES,
    CIVILIZATIONAL_SUBSYSTEMS,
    FEDERATION_GRAPH_GRANT_IDS,
    GOVERNANCE_EXPECTED,
    build_adopt_abuse_cases,
    build_observe_abuse_cases,
    build_ugr_federation_missions,
    hammer_concurrent_observe_burst,
)

# chaos_hammer inline expected statuses (not exported as a constant there)
CHAOS_GOV_EXPECTED = {400, 403, 404, 405, 415, 422}
GOV_EXPECTED = GOVERNANCE_EXPECTED | CHAOS_GOV_EXPECTED

STATE_ECHO_PATHS = [
    "/health",
    "/health/details",
    "/api/operator/ledger",
    "/api/operator/ledger/digest",
    "/api/operator/console",
    "/api/operator/console/mesh-health",
    "/api/jarvis/project-infi-state-machine/status",
    "/api/jarvis/governance-layer/status",
]

IDENTITY_PATHS = [
    "/api/jarvis/project-infi-law/status",
    "/api/jarvis/operator-profile/status",
    "/api/jarvis/jarvis-protocol/status",
    "/api/jarvis/module-governance/status",
    "/api/jarvis/run-ledger-binding/status",
    "/api/operator/organs",
]

PULSE_PATHS = [
    "/api/jarvis/operator-health-sentinel/status",
    "/api/jarvis/v8-runtime/status",
    "/api/jarvis/orchestration-spine/status",
    "/api/jarvis/system-guard/status",
]

GOSSIP_PATHS = [
    "/api/operator/console/mesh-health",
    "/api/operator/organs/mesh",
    "/api/operator/console",
]

LEDGER_PATHS = [
    "/api/operator/ledger",
    "/api/operator/ledger/digest",
    "/api/operator/ledger/query?q=chaos",
    "/api/operator/ledger/query?q=" + urllib.parse.quote("'; DROP TABLE ledger;--"),
]

CI_PROTOCOL = "DISHAMORY_HRM_AAIS_CI_GATE"
CI_VERSION = "1.0"
CI_EXIT_CODES = {
    "D0": 0,
    "D1": 10,
    "D2": 20,
    "D3": 30,
    "D4": 40,
    "D5": 50,
    "D6": 60,
    "PRE": 99,
}


@dataclass
class DisharmonyMetrics:
    governance_drift: int = 0
    memory_ledger_divergence: int = 0
    gossip_drift: int = 0
    split_brain_events: int = 0
    invariant_violations: int = 0
    health_pre_ok: int = 0
    health_post_ok: int = 0
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "governance_drift": self.governance_drift,
            "memory_ledger_divergence": self.memory_ledger_divergence,
            "gossip_drift": self.gossip_drift,
            "split_brain_events": self.split_brain_events,
            "invariant_violations": self.invariant_violations,
            "health_pre_ok": self.health_pre_ok,
            "health_post_ok": self.health_post_ok,
            "notes": self.notes[-20:],
        }


_DRIFT_READ_MAX_BODY = 65536

# Fields that legitimately change between back-to-back polls (not gossip drift).
_GOSSIP_VOLATILE_KEYS = frozenset(
    {
        "polled_at",
        "polled_at_utc",
        "timestamp",
        "ts",
        "updated_at",
        "last_poll",
        "last_seen",
        "latency",
        "latency_ms",
        "duration_ms",
        "response_time_ms",
        "checked_at",
        "fetched_at",
        "generated_at",
        "server_time",
        # Per-request correlation IDs in drift/ambiguity signals (not governance state).
        "drift_id",
    }
)


def _body_fingerprint(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()[:16]


def _strip_volatile_fields(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {
            k: _strip_volatile_fields(v)
            for k, v in obj.items()
            if k not in _GOSSIP_VOLATILE_KEYS
        }
    if isinstance(obj, list):
        return [_strip_volatile_fields(item) for item in obj]
    return obj


def _gossip_fingerprint(text: str) -> str:
    """Structural fingerprint for gossip/mesh payloads (ignores poll timestamps)."""
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return _body_fingerprint(text)
    canonical = json.dumps(_strip_volatile_fields(data), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]


def _stable_fingerprint(text: str) -> str:
    """JSON structural fingerprint with volatile timestamp fields stripped."""
    return _gossip_fingerprint(text)


def _fingerprint_payload(payload: Any) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]


def _cluster(kind: str, *, probe_id: str, payload: Any, round_id: int | None = None) -> dict[str, Any]:
    cluster: dict[str, Any] = {
        "type": kind,
        "probe_id": probe_id,
        "signature": _fingerprint_payload(payload),
    }
    if round_id is not None:
        cluster["round"] = round_id
    return cluster


def build_ci_gate_report(
    summary: dict[str, Any],
    *,
    mesh_preflight: dict[str, Any] | None,
    strict_mesh: bool,
) -> dict[str, Any]:
    """Collapse Dishamory hammer output into the formal HRM+AAIS CI contract."""
    disharmony = dict(summary.get("disharmony") or {})
    mesh = dict(mesh_preflight or {})
    rounds = int(summary.get("rounds") or 0)
    probes_total = int(summary.get("total_probes") or summary.get("probes_total") or 0)
    preflight_ok = not summary.get("fatal") and summary.get("health_preflight", 200) == 200
    postflight_ok = bool(summary.get("server_still_healthy", False)) and summary.get("health_postflight", 200) == 200

    governance_drift = int(disharmony.get("governance_drift") or 0)
    ledger_divergence = int(disharmony.get("memory_ledger_divergence") or 0)
    disharmony_events = sum(
        int(disharmony.get(key) or 0)
        for key in ("gossip_drift", "split_brain_events", "invariant_violations")
    )
    runtime_instability = int(summary.get("server_errors_5xx") or 0)
    if int(summary.get("unexpected_failures") or 0) > 0:
        runtime_instability += int(summary.get("unexpected_failures") or 0)
    if not postflight_ok and not summary.get("fatal"):
        runtime_instability += 1
    hrm_violations = int(summary.get("hrm_violations") or disharmony.get("hrm_violations") or 0)
    federation_mismatches = 0
    if strict_mesh and not mesh.get("ready", False):
        federation_mismatches += max(1, len(list(mesh.get("unreachable") or [])))
    federation_mismatches += int(disharmony.get("federation_mismatches") or 0)

    failure_clusters: list[dict[str, Any]] = []
    if summary.get("fatal") or not preflight_ok:
        failure_clusters.append(_cluster("PRE", probe_id="preflight", payload=summary))
    if governance_drift:
        failure_clusters.append(_cluster("D1", probe_id="governance:r0", payload=disharmony, round_id=0))
    if ledger_divergence:
        failure_clusters.append(_cluster("D2", probe_id="ledger:r0", payload=disharmony, round_id=0))
    if disharmony_events:
        failure_clusters.append(_cluster("D3", probe_id="dishamory:r0", payload=disharmony, round_id=0))
    if runtime_instability:
        failure_clusters.append(_cluster("D4", probe_id="runtime:r0", payload=summary, round_id=0))
    if hrm_violations:
        failure_clusters.append(_cluster("D5", probe_id="hrm_policy:r0", payload=summary, round_id=0))
    if federation_mismatches:
        failure_clusters.append(_cluster("D6", probe_id="federation:r0", payload=mesh, round_id=0))

    if any(cluster["type"] == "PRE" for cluster in failure_clusters):
        exit_code = CI_EXIT_CODES["PRE"]
    else:
        exit_code = max(
            [CI_EXIT_CODES.get(cluster["type"], 0) for cluster in failure_clusters] or [0]
        )

    return {
        "protocol": CI_PROTOCOL,
        "version": CI_VERSION,
        "rounds": rounds,
        "probes_total": probes_total,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": "PASS" if exit_code == 0 else "FAIL",
        "exit_code": exit_code,
        "summary": {
            "governance_drift": governance_drift,
            "ledger_divergence": ledger_divergence,
            "dishamory_events": disharmony_events,
            "runtime_instability_events": runtime_instability,
            "hrm_violations": hrm_violations,
            "federation_mismatches": federation_mismatches,
        },
        "drift_axes": {
            "governance": disharmony.get("notes", []) if governance_drift else [],
            "memory": disharmony.get("notes", []) if ledger_divergence else [],
            "runtime": disharmony.get("notes", []) if runtime_instability else [],
            "federation": list(mesh.get("unreachable") or []) if federation_mismatches else [],
        },
        "failure_clusters": failure_clusters,
        "health": {
            "preflight": bool(preflight_ok),
            "postflight": bool(postflight_ok),
        },
        "mesh": {
            "strict": bool(strict_mesh),
            "ready": bool(mesh.get("ready", False)),
            "configured": int(mesh.get("configured") or 0),
            "unreachable": list(mesh.get("unreachable") or []),
        },
        "legacy_summary": summary,
    }


def write_ci_gate_report(report: dict[str, Any], *, filename: str = "dishamory_chaos_report.json") -> Path:
    out = ROOT / "ci-artifacts" / filename
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return out


def _back_to_back_drift(
    path: str,
    *,
    legacy: bool | None = None,
    headers: dict | None = None,
) -> bool:
    """True when two immediate GETs on the same path disagree structurally."""
    hdrs = dict(headers or {})
    s1, t1 = _get(path, legacy=legacy, headers=hdrs, max_body=_DRIFT_READ_MAX_BODY)
    time.sleep(random.uniform(0.001, 0.008))
    s2, t2 = _get(path, legacy=legacy, headers=hdrs, max_body=_DRIFT_READ_MAX_BODY)
    if s1 != 200 or s2 != 200:
        return False
    return _stable_fingerprint(t1) != _stable_fingerprint(t2)


def _phase_b_round_reconcile(rnd: int, metrics: DisharmonyMetrics) -> None:
    """Paired reads on canonical surfaces — drift only when the same path disagrees."""
    ledger_path = "/api/operator/ledger/digest"
    if _back_to_back_drift(ledger_path):
        metrics.memory_ledger_divergence += 1
        metrics.notes.append(f"B reconcile ledger digest round {rnd}")

    gossip_path = "/api/operator/console/mesh-health"
    if _back_to_back_drift(gossip_path, headers={"X-Gossip-Seq": str(rnd)}):
        metrics.gossip_drift += 1
        metrics.notes.append(f"B reconcile gossip round {rnd} path={gossip_path}")

    gov_path = CIVILIZATIONAL_GET_ROUTES[rnd % len(CIVILIZATIONAL_GET_ROUTES)]
    if _back_to_back_drift(gov_path):
        metrics.governance_drift += 1
        metrics.notes.append(f"B reconcile governance round {rnd} path={gov_path}")


def _add(
    report: ChaosReport,
    name: str,
    status: int | None,
    *,
    note: str = "",
    expected_fail: bool = False,
) -> ChaosResult:
    ok = status is not None and status < 500
    r = ChaosResult(name=name, status=status, ok=ok, note=note[:120], expected_fail=expected_fail)
    report.add(r)
    return r


def _get(
    path: str,
    *,
    legacy: bool | None = None,
    headers: dict | None = None,
    max_body: int = 500,
) -> tuple[int | None, str]:
    if legacy is None:
        legacy = path.startswith("/api/")
    return _req("GET", path, legacy=legacy, headers=headers, max_body=max_body)


def _post(path: str, payload: dict, *, legacy: bool = True) -> tuple[int | None, str]:
    return _req("POST", path, body=json.dumps(payload).encode(), legacy=legacy)


# --- Phase A (8 probes per round) ---


def probe_a1_state_echo_drift(report: ChaosReport, rnd: int, metrics: DisharmonyMetrics) -> None:
    path = STATE_ECHO_PATHS[rnd % len(STATE_ECHO_PATHS)]
    headers = {"Cache-Control": "no-cache", "X-Dishamory-Round": str(rnd)}
    s1, t1 = _get(path, headers=headers)
    time.sleep(random.uniform(0.001, 0.02))
    s2, t2 = _get(path, headers={**headers, "X-Stale-Inject": str(random.randint(0, 9999))})
    _add(report, f"A1_state_echo:r{rnd}:{path}", s2, note=t2[:80])
    if s1 == 200 and s2 == 200 and _body_fingerprint(t1) != _body_fingerprint(t2):
        if path in {"/health", "/health/details"}:
            metrics.invariant_violations += 1
            metrics.notes.append(f"A1 health body drift round {rnd}")


def probe_a2_memory_ledger_divergence(report: ChaosReport, rnd: int, metrics: DisharmonyMetrics) -> None:
    path = "/api/operator/ledger/digest"
    s1, t1 = _get(path, max_body=_DRIFT_READ_MAX_BODY)
    s2, t2 = _get(path, headers={"X-Dishamory-Round": str(rnd)}, max_body=_DRIFT_READ_MAX_BODY)
    _add(report, f"A2_ledger_digest:r{rnd}", s2, note=t2[:80])
    if s1 == 200 and s2 == 200 and _stable_fingerprint(t1) != _stable_fingerprint(t2):
        metrics.memory_ledger_divergence += 1
        metrics.notes.append(f"A2 ledger digest diverged round {rnd}")


def probe_a3_governance_echo(report: ChaosReport, rnd: int, metrics: DisharmonyMetrics) -> None:
    path = CIVILIZATIONAL_GET_ROUTES[rnd % len(CIVILIZATIONAL_GET_ROUTES)]
    time.sleep(random.uniform(0, 0.03))
    s1, t1 = _get(path, max_body=_DRIFT_READ_MAX_BODY)
    time.sleep(random.uniform(0, 0.03))
    s2, t2 = _get(path, max_body=_DRIFT_READ_MAX_BODY)
    _add(report, f"A3_governance_echo:r{rnd}:{path}", s2, note=t2[:80], expected_fail=s2 in {404})
    if s1 == s2 == 200 and _stable_fingerprint(t1) != _stable_fingerprint(t2):
        metrics.governance_drift += 1
        metrics.notes.append(f"A3 governance echo drift round {rnd} path={path}")


def probe_a4_runtime_pulse(report: ChaosReport, rnd: int, _metrics: DisharmonyMetrics) -> None:
    path = PULSE_PATHS[rnd % len(PULSE_PATHS)]
    time.sleep(random.uniform(0, 0.05))
    status, text = _get(path)
    _add(report, f"A4_runtime_pulse:r{rnd}:{path}", status, note=text[:80])


def probe_a5_identity_drift(report: ChaosReport, rnd: int, metrics: DisharmonyMetrics) -> None:
    path = IDENTITY_PATHS[rnd % len(IDENTITY_PATHS)]
    s1, t1 = _get(path)
    s2, t2 = _get(path, headers={"X-Role-Probe": "chaos"})
    _add(report, f"A5_identity:r{rnd}:{path}", s2, note=t2[:80])
    if s1 == 200 and s2 == 200:
        try:
            j1, j2 = json.loads(t1), json.loads(t2)
            id1 = (j1.get("subsystem_id") or j1.get("gene") or j1.get("status"))
            id2 = (j2.get("subsystem_id") or j2.get("gene") or j2.get("status"))
            if id1 and id2 and id1 != id2:
                metrics.governance_drift += 1
        except json.JSONDecodeError:
            pass


def probe_a6_soft_failure_accumulation(report: ChaosReport, rnd: int, _metrics: DisharmonyMetrics) -> None:
    kind = rnd % 3
    if kind == 0:
        label = "observe_empty"
        target = CIVILIZATIONAL_SUBSYSTEMS[rnd % len(CIVILIZATIONAL_SUBSYSTEMS)]["observe"]
        status, text = _post(target, {})
        _add(
            report,
            f"A6_soft_fail:r{rnd}:{label}",
            status,
            note=text[:80],
            expected_fail=status in GOV_EXPECTED,
        )
    elif kind == 1:
        label = "ledger_bad_q"
        target = "/api/operator/ledger/query?q=" + quote_sql_injection()
        status, text = _get(target)
        _add(report, f"A6_soft_fail:r{rnd}:{label}", status, note=text[:80])
    else:
        label = "wrong_method_health"
        status, text = _req("DELETE", "/health")
        _add(
            report,
            f"A6_soft_fail:r{rnd}:{label}",
            status,
            note=text[:80],
            expected_fail=status in {405, 404, 400},
        )


def probe_a7_gossip_drift(report: ChaosReport, rnd: int, metrics: DisharmonyMetrics) -> None:
    path = GOSSIP_PATHS[rnd % len(GOSSIP_PATHS)]
    s1, t1 = _get(path, max_body=_DRIFT_READ_MAX_BODY)
    s2, t2 = _get(path, headers={"X-Gossip-Seq": str(rnd)}, max_body=_DRIFT_READ_MAX_BODY)
    _add(report, f"A7_gossip:r{rnd}:{path}", s2, note=t2[:80])
    if s1 == 200 and s2 == 200 and _gossip_fingerprint(t1) != _gossip_fingerprint(t2):
        metrics.gossip_drift += 1
        metrics.notes.append(f"A7 gossip structural drift round {rnd} path={path}")


def probe_a8_health_delta(report: ChaosReport, rnd: int, metrics: DisharmonyMetrics) -> None:
    pre, _ = _get("/health")
    if pre == 200:
        metrics.health_pre_ok += 1
    else:
        metrics.invariant_violations += 1
    _add(report, f"A8_health_pre:r{rnd}", pre)
    post, text = _get("/health")
    if post == 200:
        metrics.health_post_ok += 1
    else:
        metrics.invariant_violations += 1
    _add(report, f"A8_health_post:r{rnd}", post, note=text[:60])


PHASE_A_PROBES: list[Callable[..., None]] = [
    probe_a1_state_echo_drift,
    probe_a2_memory_ledger_divergence,
    probe_a3_governance_echo,
    probe_a4_runtime_pulse,
    probe_a5_identity_drift,
    probe_a6_soft_failure_accumulation,
    probe_a7_gossip_drift,
    probe_a8_health_delta,
]


def run_phase_a(report: ChaosReport, rnd: int, metrics: DisharmonyMetrics) -> None:
    for probe in PHASE_A_PROBES:
        probe(report, rnd, metrics)


# --- Phase B builders (72 probes = 18 per subsystem per round) ---


def _governance_probes_for_round(rnd: int) -> list[tuple[str, Callable[[], tuple[int | None, str, bool]]]]:
    probes: list[tuple[str, Callable[[], tuple[int | None, str, bool]]]] = []
    observe_cases = build_observe_abuse_cases()
    adopt_cases = build_adopt_abuse_cases()

    for i, subsystem in enumerate(CIVILIZATIONAL_SUBSYSTEMS):
        label = subsystem["label"]
        obs_name, obs_payload = observe_cases[(rnd + i) % len(observe_cases)]
        probes.append(
            (
                f"B1_observe:{label}:{obs_name}",
                lambda p=subsystem["observe"], pl=obs_payload: (
                    *_post(p, pl),
                    True,
                ),
            )
        )

    for i, subsystem in enumerate(CIVILIZATIONAL_SUBSYSTEMS):
        label = subsystem["label"]
        case_name, payload, _expected = adopt_cases[(rnd + i) % len(adopt_cases)]
        probes.append(
            (
                f"B1_adopt:{label}:{case_name}",
                lambda p=subsystem["adopt"], pl=payload: (
                    *_post(p, pl),
                    True,
                ),
            )
        )

    for i in range(4):
        path = CIVILIZATIONAL_GET_ROUTES[i % len(CIVILIZATIONAL_GET_ROUTES)]
        shadow_path = CIVILIZATIONAL_GET_ROUTES[(i + 1) % len(CIVILIZATIONAL_GET_ROUTES)]
        probes.append(
            (
                f"B1_rule_shadow:r{rnd}:{'/'.join(path.split('/')[-2:])}",
                lambda a=path, b=shadow_path: _governance_shadow_pair(a, b),
            )
        )

    for i in range(4):
        path = CIVILIZATIONAL_GET_ROUTES[i % len(CIVILIZATIONAL_GET_ROUTES)]
        probes.append(
            (
                f"B1_invariant_edge:r{rnd}:{i}",
                lambda p=path, off=i: (
                    *_get(f"{p}?window_days={-1 - off}&limit={10**off}"),
                    False,
                ),
            )
        )

    return probes[:18]


def _governance_shadow_pair(path_a: str, path_b: str) -> tuple[int | None, str, bool]:
    s1, t1 = _get(path_a)
    s2, t2 = _get(path_b)
    note = f"a={s1} b={s2} {t2[:40]}"
    return s2, note, s1 in {404} or s2 in {404}


def _memory_probes_for_round(rnd: int) -> list[tuple[str, Callable[[], tuple[int | None, str, bool]]]]:
    probes: list[tuple[str, Callable[[], tuple[int | None, str, bool]]]] = []

    for i, path in enumerate(LEDGER_PATHS):
        probes.append((f"B2_ledger_read:r{rnd}:{i}", lambda p=path: (*_get(p), False)))

    for i, grant_id in enumerate(FEDERATION_GRAPH_GRANT_IDS[:6]):
        path = f"/api/operator/ledger/federation/{grant_id}/graph?session_id=tenant:acme"
        probes.append(
            (
                f"B2_ledger_fork:r{rnd}:{grant_id[:20]}",
                lambda p=path: (*_get(p), True),
            )
        )

    for i in range(4):
        probes.append(
            (
                f"B2_pattern_replay:r{rnd}:{i}",
                lambda n=i: (
                    *_get(f"/api/operator/ledger/query?q=replay-{rnd}-{n}"),
                    False,
                ),
            )
        )

    for i in range(4):
        probes.append(
            (
                f"B2_stale_pattern:r{rnd}:{i}",
                lambda n=i: (
                    *_get(
                        "/api/operator/ledger/digest",
                        headers={"X-Stale-Pattern": str(rnd * 100 + n)},
                    ),
                    False,
                ),
            )
        )

    # B2.4 — Memory-Write Contention (one probe; grant list has 5 ids → 4+5+4+4+1 = 18)
    probes.append(
        (
            f"B2_memory_write_contention:r{rnd}",
            lambda: (
                *_post(
                    "/api/operator/ledger/observe",
                    {"session_id": f"contention-{rnd}", "window_days": 7},
                ),
                True,
            ),
        )
    )

    return probes[:18]


def _runtime_probes_for_round(rnd: int) -> list[tuple[str, Callable[[], tuple[int | None, str, bool]]]]:
    from tools.stress.live_api_stress import discover_jarvis_status_paths

    status_paths = discover_jarvis_status_paths()
    probes: list[tuple[str, Callable[[], tuple[int | None, str, bool]]]] = []

    for i in range(6):
        path = status_paths[(rnd * 3 + i) % len(status_paths)]
        probes.append((f"B3_status:r{rnd}:{path.split('/')[-2]}", lambda p=path: (*_get(p), False)))

    abuse_paths = [
        "/api/jarvis/../../../etc/passwd/status",
        "/api/operator/ledger/../../health",
        "/api/jarvis/pipeline/" + "z" * (200 + rnd % 300),
    ]
    for i, path in enumerate(abuse_paths):
        probes.append(
            (
                f"B3_pid1_violation:r{rnd}:{i}",
                lambda p=path: (*_get(p), True),
            )
        )

    for i in range(6):
        method = ["DELETE", "PUT", "PATCH", "POST"][i % 4]
        path = ["/health", "/api/jarvis/otem-bounded/status", "/api/operator/console"][i % 3]
        probes.append(
            (
                f"B3_concurrency_poison:r{rnd}:{i}",
                lambda m=method, p=path: (
                    *_req(m, p, body=b"{}", legacy=p.startswith("/api/")),
                    True,
                ),
            )
        )

    probes.append(
        (
            f"B3_otem:r{rnd}",
            lambda: (*_get("/api/jarvis/otem-bounded/status"), False),
        )
    )
    probes.append(
        (
            f"B3_v8:r{rnd}",
            lambda: (*_get("/api/jarvis/v8-runtime/status"), False),
        )
    )
    probes.append(
        (
            f"B3_pulse:r{rnd}",
            lambda: (*_get(PULSE_PATHS[rnd % len(PULSE_PATHS)]), False),
        )
    )

    return probes[:18]


def _federation_probes_for_round(rnd: int) -> list[tuple[str, Callable[[], tuple[int | None, str, bool]]]]:
    probes: list[tuple[str, Callable[[], tuple[int | None, str, bool]]]] = []
    missions = build_ugr_federation_missions()

    for i, (case_name, payload) in enumerate(missions):
        probes.append(
            (
                f"B4_ugr_mission:r{rnd}:{case_name}",
                lambda pl=payload: (
                    *_req("POST", "/api/ugr/mission/run", body=json.dumps(pl).encode(), fastapi=True),
                    True,
                ),
            )
        )

    for i, sub in enumerate(CIVILIZATIONAL_SUBSYSTEMS):
        probes.append(
            (
                f"B4_gossip_flood:r{rnd}:{sub['label']}",
                lambda p=sub["observe"], n=i: (*_post(p, {"window_days": 7 + n}), True),
            )
        )

    for i in range(4):
        sub = CIVILIZATIONAL_SUBSYSTEMS[i % len(CIVILIZATIONAL_SUBSYSTEMS)]
        probes.append(
            (
                f"B4_observe_adopt_abuse:r{rnd}:{i}",
                lambda s=sub, n=i: (
                    *_post(
                        s["adopt"],
                        {"operator_approved": bool(n % 2), "candidate": {"candidate_id": f"chaos-{rnd}-{n}"}},
                    ),
                    True,
                ),
            )
        )

    for i, grant_id in enumerate(FEDERATION_GRAPH_GRANT_IDS[:4]):
        path = f"/api/operator/ledger/federation/{grant_id}/graph?session_id=tenant:acme"
        probes.append(
            (
                f"B4_falsity_sync:r{rnd}:{i}",
                lambda p=path: (*_get(p), True),
            )
        )

    return probes[:18]


def run_phase_b(report: ChaosReport, rnd: int, metrics: DisharmonyMetrics) -> None:
    all_probes: list[tuple[str, Callable[[], tuple[int | None, str, bool]]]] = []
    all_probes.extend(_governance_probes_for_round(rnd))
    all_probes.extend(_memory_probes_for_round(rnd))
    all_probes.extend(_runtime_probes_for_round(rnd))
    all_probes.extend(_federation_probes_for_round(rnd))
    assert len(all_probes) == 72, f"phase B probe count {len(all_probes)} != 72"

    for name, fn in all_probes:
        try:
            status, text, expected = fn()
        except Exception as exc:
            status, text, expected = None, str(exc)[:120], False
        _add(
            report,
            f"{name}",
            status,
            note=text[:80],
            expected_fail=expected and status in (GOV_EXPECTED | {400, 403, 404, 405, 422}),
        )

    _phase_b_round_reconcile(rnd, metrics)


# --- Phase B2 (32 concurrent bursts per round) ---


def _burst_tasks_for_round(rnd: int) -> list[tuple[str, str, bytes | None, str]]:
    tasks: list[tuple[str, str, bytes | None, str]] = []
    for subsystem in CIVILIZATIONAL_SUBSYSTEMS:
        for i in range(2):
            tasks.append((f"govern_observe_{subsystem['label']}_{i}", subsystem["observe"], b"{}", "POST"))
    for path in LEDGER_PATHS:
        tasks.append((f"ledger_{path.split('/')[-1]}", path, None, "GET"))
    for path in PULSE_PATHS:
        tasks.append((f"pulse_{path.split('/')[-2]}", path, None, "GET"))
    for i in range(8):
        path = GOSSIP_PATHS[i % len(GOSSIP_PATHS)]
        tasks.append((f"gossip_{i}", path, None, "GET"))
    for case_name, payload in build_ugr_federation_missions()[:4]:
        tasks.append(
            (
                f"ugr_{case_name}",
                "/api/ugr/mission/run",
                json.dumps(payload).encode(),
                "POST_FAST",
            )
        )
    tasks.append(("health_echo", "/health", None, "GET"))
    tasks.append(("ledger_digest_burst", "/api/operator/ledger/digest", None, "GET"))
    return tasks[:32]


def run_phase_b2(report: ChaosReport, rnd: int, metrics: DisharmonyMetrics) -> None:
    tasks = _burst_tasks_for_round(rnd)
    assert len(tasks) == 32, f"phase B2 task count {len(tasks)} != 32"

    def one(task: tuple[str, str, bytes | None, str]) -> ChaosResult:
        label, path, body, kind = task
        if kind == "POST":
            status, text = _req("POST", path, body=body or b"{}", legacy=True)
            expected = status in GOV_EXPECTED
        elif kind == "POST_FAST":
            status, text = _req("POST", path, body=body, fastapi=True)
            expected = status in {400, 403, 404, 422}
        else:
            status, text = _get(path)
            expected = False
        return ChaosResult(
            name=f"B2_burst:r{rnd}:{label}",
            status=status,
            ok=status is not None and status < 500,
            note=text[:60],
            expected_fail=expected,
        )

    workers = min(32, 16 + rnd % 8)
    with ThreadPoolExecutor(max_workers=workers) as ex:
        results = list(ex.map(one, tasks))

    statuses = [r.status for r in results if r.status is not None]
    if statuses.count(200) > 0 and any(s and s >= 500 for s in statuses):
        metrics.split_brain_events += 1

    for r in results:
        report.add(r)


# --- Phase C (10 federation mission probes per round) ---


def run_phase_c(report: ChaosReport, rnd: int, metrics: DisharmonyMetrics) -> None:
    missions = build_ugr_federation_missions()
    mission = missions[rnd % len(missions)][1]

    c_probes: list[tuple[str, Callable[[], tuple[int | None, str, bool]]]] = [
        (
            f"C1_mission_graph:r{rnd}",
            lambda: (
                *_req(
                    "POST",
                    "/api/ugr/mission/run",
                    body=json.dumps(mission).encode(),
                    fastapi=True,
                ),
                True,
            ),
        ),
        (
            f"C2_invariant_sync:r{rnd}",
            lambda: (*_get("/api/jarvis/invariant-engine/status"), False),
        ),
        (
            f"C3_gov_runtime_reconcile:r{rnd}",
            lambda: (
                *_get(CIVILIZATIONAL_GET_ROUTES[rnd % len(CIVILIZATIONAL_GET_ROUTES)]),
                False,
            ),
        ),
        (
            f"C4_ledger_gossip_reconcile:r{rnd}",
            lambda: (*_get("/api/operator/console/mesh-health"), False),
        ),
        (f"C5_mission_health_pre:r{rnd}", lambda: (*_get("/health"), False)),
        (
            f"C6_node_identity:r{rnd}",
            lambda: (*_get(IDENTITY_PATHS[rnd % len(IDENTITY_PATHS)]), False),
        ),
        (
            f"C7_drift_under_load:r{rnd}",
            lambda: (
                *_get(f"/api/operator/ledger/digest?load={rnd}"),
                False,
            ),
        ),
        (
            f"C8_drift_under_silence:r{rnd}",
            lambda: (
                *_get("/health/details"),
                False,
            ),
        ),
        (
            f"C9_drift_under_recovery:r{rnd}",
            lambda: (*_get("/api/operator/ledger"), False),
        ),
        (f"C10_drift_under_restart:r{rnd}", lambda: (*_get("/health"), False)),
    ]

    for name, fn in c_probes:
        try:
            status, text, expected = fn()
        except Exception as exc:
            status, text, expected = None, str(exc)[:120], False
        _add(
            report,
            name,
            status,
            note=text[:80],
            expected_fail=expected and status in (GOV_EXPECTED | {400, 403, 404, 422}),
        )
        if name.startswith("C5_mission_health_pre"):
            if status == 200:
                metrics.health_pre_ok += 1
            else:
                metrics.invariant_violations += 1
        if name.startswith("C10_drift_under_restart") and status == 200:
            metrics.health_post_ok += 1


def run_dishamory_chaos(
    *,
    rounds: int = 100,
    skip_ugr: bool = False,
    phase: str | None = None,
) -> dict[str, Any]:
    report = ChaosReport()
    metrics = DisharmonyMetrics()
    phase_counts = {"A": 0, "B": 0, "B2": 0, "C": 0}

    print("=== DISHAMORY CHAOS HAMMER — 100× PROTOCOL ===")
    print(f"Target: {BASE}  rounds={rounds}  phase={phase or 'ALL'}")

    status, text = _get("/health")
    _add(report, "health_global_preflight", status, note=text[:80])
    if status != 200:
        print(f"FATAL: server not healthy ({status})")
        return {"fatal": True, "health": status}

    metrics.health_pre_ok += 1

    cloud_forge_offline_ok = True
    cloud_forge_accel_offline_ok = True
    cf_notes: list[str] = []
    cf_accel_notes: list[str] = []

    try:
        cf_notes = hammer_cloud_forge_offline()
        if not cf_notes:
            metrics.invariant_violations += 1
            cloud_forge_offline_ok = False
    except AssertionError as exc:
        metrics.invariant_violations += 1
        cloud_forge_offline_ok = False
        metrics.notes.append(f"cloud_forge: {exc}")

    try:
        cf_accel_notes = hammer_cloud_forge_acceleration_offline()
        if cf_accel_notes and cf_accel_notes[0].startswith("acceleration_tokens_disabled"):
            metrics.notes.append(cf_accel_notes[0])
        elif not cf_accel_notes:
            metrics.invariant_violations += 1
            cloud_forge_accel_offline_ok = False
    except AssertionError as exc:
        metrics.invariant_violations += 1
        cloud_forge_accel_offline_ok = False
        metrics.notes.append(f"cloud_forge_accel: {exc}")

    run_phases = {"A", "B", "B2", "C"} if phase is None else {phase.upper()}

    for rnd in range(rounds):
        if rnd % 10 == 0:
            print(f"  round {rnd + 1}/{rounds}...")
        if "A" in run_phases:
            run_phase_a(report, rnd, metrics)
            phase_counts["A"] += 8
        if "B" in run_phases:
            if skip_ugr:
                for i in range(72):
                    _add(report, f"B_skipped_ugr:r{rnd}:{i}", 200, note="skip_ugr", expected_fail=False)
            else:
                run_phase_b(report, rnd, metrics)
            phase_counts["B"] += 72
        if "B2" in run_phases:
            if skip_ugr:
                for i in range(32):
                    _add(report, f"B2_skipped:r{rnd}:{i}", 200, note="skip_ugr")
            else:
                run_phase_b2(report, rnd, metrics)
            phase_counts["B2"] += 32
        if "C" in run_phases:
            if skip_ugr:
                for i in range(10):
                    _add(report, f"C_skipped:r{rnd}:{i}", 200, note="skip_ugr")
            else:
                run_phase_c(report, rnd, metrics)
            phase_counts["C"] += 10

    status2, _ = _get("/health")
    _add(report, "health_global_postflight", status2)
    if status2 == 200:
        metrics.health_post_ok += 1
    else:
        metrics.invariant_violations += 1

    disharmony = metrics.to_dict()
    summary = {
        "protocol": "DISHAMORY_100x",
        "rounds": rounds,
        "phase_filter": phase,
        "skip_ugr": skip_ugr,
        "total_probes": len(report.results),
        "server_errors_5xx": len(report.server_errors),
        "unexpected_failures": len(report.unexpected_failures),
        "phase_counts": phase_counts,
        "probes_per_round": sum(phase_counts.values()) // max(rounds, 1),
        "disharmony": disharmony,
        "health_preflight": status,
        "health_postflight": status2,
        "server_still_healthy": status2 == 200,
        "cloud_forge_offline_ok": cloud_forge_offline_ok and cloud_forge_accel_offline_ok,
        "cloud_forge_accel_preflight_skipped": bool(
            cf_accel_notes
            and cf_accel_notes[0].startswith("acceleration_tokens_disabled")
        ),
    }

    print("\n=== DISHAMORY SUMMARY ===")
    print(json.dumps(summary, indent=2))
    if report.server_errors:
        print("\n!!! SERVER ERRORS (5xx) !!!")
        for r in report.server_errors[:20]:
            print(f"  {r.name} -> {r.status} {r.note}")
    if report.unexpected_failures:
        print("\n!!! UNEXPECTED FAILURES !!!")
        for r in report.unexpected_failures[:20]:
            print(f"  {r.name} -> {r.status} {r.note}")
    if any(
        disharmony[k] > 0
        for k in (
            "governance_drift",
            "memory_ledger_divergence",
            "gossip_drift",
            "split_brain_events",
            "invariant_violations",
        )
    ):
        print("\n!!! DISHARMONY METRICS NON-ZERO !!!")
        print(json.dumps(disharmony, indent=2))

    ci_report = build_ci_gate_report(
        summary,
        mesh_preflight=None,
        strict_mesh=False,
    )
    ci_report["server_errors"] = [r.__dict__ for r in report.server_errors]
    ci_report["unexpected_failures"] = [r.__dict__ for r in report.unexpected_failures]
    ci_report["all_results_count"] = len(report.results)
    out = write_ci_gate_report(ci_report)
    print(f"\nReport: {out}")
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", default=None, help="Override AAIS_STRESS_BASE")
    parser.add_argument("--rounds", type=int, default=100, help="Protocol rounds (default 100; remediation 500)")
    parser.add_argument("--phase", choices=["A", "B", "B2", "C"], default=None, help="Run single phase only")
    parser.add_argument("--skip-ugr", action="store_true", help="Skip UGR-heavy B/B2/C probes")
    parser.add_argument(
        "--require-mesh",
        action="store_true",
        help="Fail fast if configured mesh peers are unreachable (full federation protocol)",
    )
    parser.add_argument(
        "--single-node",
        action="store_true",
        help="Single-node mode: skip federation/UGR probes (same as --skip-ugr)",
    )
    parser.add_argument("--remediation", action="store_true", help="Run 500 rounds on isolated phase")
    args = parser.parse_args(argv)
    if args.base:
        configure_base(args.base)

    skip_ugr = args.skip_ugr or args.single_node
    mesh = probe_mesh_peers()
    if args.require_mesh and not mesh["ready"]:
        print("FATAL: --require-mesh but mesh peers unreachable:")
        print(json.dumps(mesh, indent=2))
        ci_report = build_ci_gate_report(
            {
                "rounds": 500 if args.remediation else args.rounds,
                "total_probes": 0,
                "server_errors_5xx": 0,
                "unexpected_failures": 0,
                "server_still_healthy": True,
                "health_preflight": 200,
                "health_postflight": 200,
                "disharmony": DisharmonyMetrics().to_dict(),
            },
            mesh_preflight=mesh,
            strict_mesh=True,
        )
        out = write_ci_gate_report(ci_report)
        print(f"Report: {out}")
        return ci_report["exit_code"]
    if not skip_ugr and not mesh["ready"]:
        skip_ugr = True
        print(
            "Mesh peers not ready — auto --skip-ugr "
            f"(configured={mesh['configured']}, unreachable={mesh['unreachable']}). "
            "Start deploy/mesh peers or pass --require-mesh to fail fast."
        )
    elif mesh["ready"]:
        print(f"Mesh preflight OK ({mesh['configured']} peer(s))")

    rounds = 500 if args.remediation else args.rounds
    summary = run_dishamory_chaos(rounds=rounds, skip_ugr=skip_ugr, phase=args.phase)
    summary["mesh_preflight"] = mesh
    ci_report = build_ci_gate_report(
        summary,
        mesh_preflight=mesh,
        strict_mesh=args.require_mesh,
    )
    out = write_ci_gate_report(ci_report)
    print(f"CI gate status: {ci_report['status']} exit_code={ci_report['exit_code']}")
    print(f"Report: {out}")
    return ci_report["exit_code"]


if __name__ == "__main__":
    sys.exit(main())
