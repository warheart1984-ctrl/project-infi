#!/usr/bin/env python
"""Federation-grade chaos harness — civilizational arc + UGR cross-tenant abuse."""

from __future__ import annotations

import argparse
import json
import sys
import urllib.parse
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.stress._chaos_common import (  # noqa: E402
    BASE,
    ChaosReport,
    ChaosResult,
    _req,
    configure_base,
    write_chaos_report,
)

GOVERNANCE_EXPECTED = {400, 403, 405, 422}

CIVILIZATIONAL_GET_ROUTES = [
    "/api/operator/norm-federations",
    "/api/operator/norm-federations/treaties",
    "/api/operator/diplomacy",
    "/api/operator/diplomacy/accords",
    "/api/operator/constitutional-evolution",
    "/api/operator/constitutional-evolution/amendments",
    "/api/operator/civilizations",
    "/api/operator/civilizations/charters",
]

CIVILIZATIONAL_SUBSYSTEMS = [
    {
        "label": "norm_federation",
        "observe": "/api/operator/norm-federations/observe",
        "adopt": "/api/operator/norm-federations/treaties/adopt",
    },
    {
        "label": "diplomacy",
        "observe": "/api/operator/diplomacy/observe",
        "adopt": "/api/operator/diplomacy/accords/adopt",
    },
    {
        "label": "constitutional_evolution",
        "observe": "/api/operator/constitutional-evolution/observe",
        "adopt": "/api/operator/constitutional-evolution/amendments/adopt",
    },
    {
        "label": "governed_civilization",
        "observe": "/api/operator/civilizations/observe",
        "adopt": "/api/operator/civilizations/charters/adopt",
    },
]

FEDERATION_GRAPH_GRANT_IDS = [
    "smoke-grant",
    "../../../etc/passwd",
    urllib.parse.quote("'; DROP TABLE ledger;--"),
    "g" * 500,
    "grant%00null",
]


def build_observe_abuse_cases() -> list[tuple[str, dict]]:
    return [
        ("empty", {}),
        ("window_negative", {"window_days": -1}),
        ("window_huge", {"window_days": 999999}),
        ("session_traversal", {"session_id": "../../../etc/passwd"}),
        ("session_overflow", {"session_id": "x" * 50000}),
    ]


def build_adopt_abuse_cases() -> list[tuple[str, dict, set[int]]]:
    return [
        ("empty_body", {}, {403}),
        (
            "approved_no_candidate",
            {"operator_approved": True},
            {403, 400},
        ),
        (
            "approved_injected_candidate",
            {
                "operator_approved": True,
                "candidate": {"candidate_id": "chaos-injected", "summary": "x" * 10000},
            },
            {403, 400},
        ),
        ("not_approved", {"operator_approved": False}, {403}),
    ]


def build_ugr_federation_missions() -> list[tuple[str, dict]]:
    base = {
        "operator_id": "operator-federation-chaos",
        "tenant_id": "tenant:acme",
        "aais_instance_id": "aais-local-1",
        "region_id": "tenant-us",
        "intent": "governed_super_router_demo",
        "objective": "Federation chaos probe",
        "steps": [
            {
                "step_id": "home-scout",
                "objective": "Home tenant scout pass",
                "organ_id": "organ-local-tiny",
            },
            {
                "step_id": "peer-relay",
                "objective": "Federated step through contoso manifold",
                "organ_id": "organ-local-tiny",
                "federation_peer_tenant": "tenant:contoso",
            },
        ],
        "halt_on_failure": True,
    }
    bogus_grant = json.loads(json.dumps(base))
    bogus_grant["steps"][1]["federation_grant_id"] = "grant-chaos-404"

    wrong_tenant = json.loads(json.dumps(bogus_grant))
    wrong_tenant["tenant_id"] = "../../../etc"

    smoke_grant = json.loads(json.dumps(bogus_grant))
    smoke_grant["steps"][1]["federation_grant_id"] = "smoke-grant"

    overflow = json.loads(json.dumps(bogus_grant))
    overflow["steps"][1]["objective"] = "x" * 10000
    overflow["steps"][1]["organ_id"] = "organ-" + ("y" * 500)

    return [
        ("missing_grant_id", base),
        ("bogus_grant_id", bogus_grant),
        ("tenant_traversal", wrong_tenant),
        ("smoke_grant_wrong_tenant", smoke_grant),
        ("overflow_federated_step", overflow),
    ]


def hammer_civilizational_surface(report: ChaosReport) -> None:
    for path in CIVILIZATIONAL_GET_ROUTES:
        status, text = _req("GET", path, legacy=True)
        report.add(
            ChaosResult(
                name=f"civilizational_get:{path}",
                status=status,
                ok=status is not None and status < 500,
                note=text[:80],
                expected_fail=status in {404},
            )
        )


def hammer_civilizational_governance(report: ChaosReport) -> None:
    observe_cases = build_observe_abuse_cases()
    adopt_cases = build_adopt_abuse_cases()

    for subsystem in CIVILIZATIONAL_SUBSYSTEMS:
        label = subsystem["label"]
        observe_path = subsystem["observe"]
        adopt_path = subsystem["adopt"]

        for case_name, payload in observe_cases:
            status, text = _req(
                "POST",
                observe_path,
                body=json.dumps(payload).encode(),
                legacy=True,
            )
            report.add(
                ChaosResult(
                    name=f"{label}_observe:{case_name}",
                    status=status,
                    ok=status is not None and status < 500,
                    note=text[:80],
                    expected_fail=status in GOVERNANCE_EXPECTED,
                )
            )

        for case_name, payload, expected in adopt_cases:
            status, text = _req(
                "POST",
                adopt_path,
                body=json.dumps(payload).encode(),
                legacy=True,
            )
            report.add(
                ChaosResult(
                    name=f"{label}_adopt:{case_name}",
                    status=status,
                    ok=status is not None and status < 500,
                    note=text[:80],
                    expected_fail=status in expected,
                )
            )

        status, text = _req("GET", adopt_path, legacy=True)
        report.add(
            ChaosResult(
                name=f"{label}_adopt_wrong_method",
                status=status,
                ok=status is not None and status < 500,
                note=text[:80],
                expected_fail=status in {405, 400, 403},
            )
        )


def hammer_concurrent_observe_burst(report: ChaosReport, *, workers: int = 16, per_endpoint: int = 8) -> None:
    tasks: list[tuple[str, str]] = []
    for subsystem in CIVILIZATIONAL_SUBSYSTEMS:
        for i in range(per_endpoint):
            tasks.append((f"{subsystem['label']}_burst_{i}", subsystem["observe"]))

    def one(task: tuple[str, str]) -> ChaosResult:
        name, path = task
        status, text = _req("POST", path, body=b"{}", legacy=True)
        return ChaosResult(
            name=f"concurrent_observe:{name}",
            status=status,
            ok=status is not None and status < 500,
            note=text[:60],
            expected_fail=status in GOVERNANCE_EXPECTED,
        )

    with ThreadPoolExecutor(max_workers=workers) as ex:
        for result in ex.map(one, tasks):
            report.add(result)


def hammer_ugr_federation(report: ChaosReport) -> None:
    for case_name, payload in build_ugr_federation_missions():
        status, text = _req(
            "POST",
            "/api/ugr/mission/run",
            body=json.dumps(payload).encode(),
            fastapi=True,
        )
        report.add(
            ChaosResult(
                name=f"ugr_federation_mission:{case_name}",
                status=status,
                ok=status is not None and status < 500,
                note=text[:100],
                expected_fail=status in {400, 403, 404, 422},
            )
        )

    for grant_id in FEDERATION_GRAPH_GRANT_IDS:
        path = f"/api/operator/ledger/federation/{grant_id}/graph?session_id=tenant:acme"
        status, text = _req("GET", path, legacy=True)
        report.add(
            ChaosResult(
                name=f"odl_federation_graph:{grant_id[:40]}",
                status=status,
                ok=status is not None and status < 500,
                note=text[:80],
                expected_fail=status in {400, 404},
            )
        )


def run_federation_chaos(*, skip_ugr: bool = False) -> dict:
    report = ChaosReport()
    print("=== FEDERATION CHAOS HAMMER — Project Infinity ===")
    print(f"Target: {BASE}")

    status, text = _req("GET", "/health")
    report.add(ChaosResult("health_preflight", status, status == 200, text[:80]))
    if status != 200:
        print(f"FATAL: server not healthy ({status})")
        return {"fatal": True, "health": status}

    print("[A] Civilizational surface farm...")
    hammer_civilizational_surface(report)
    print("[B] Civilizational governance abuse...")
    hammer_civilizational_governance(report)
    print("[B2] Concurrent observe burst...")
    hammer_concurrent_observe_burst(report)
    if skip_ugr:
        print("[C] UGR federation abuse... SKIPPED")
    else:
        print("[C] UGR federation abuse...")
        hammer_ugr_federation(report)

    status2, _ = _req("GET", "/health")
    report.add(ChaosResult("health_postflight", status2, status2 == 200))

    phase_counts = {
        "civilizational_get": sum(1 for r in report.results if r.name.startswith("civilizational_get:")),
        "civilizational_governance": sum(
            1
            for r in report.results
            if "_observe:" in r.name or "_adopt:" in r.name or "_adopt_wrong_method" in r.name
        ),
        "concurrent_observe": sum(1 for r in report.results if r.name.startswith("concurrent_observe:")),
        "ugr_federation": sum(
            1 for r in report.results if r.name.startswith(("ugr_federation_mission:", "odl_federation_graph:"))
        ),
    }

    summary = {
        "total_probes": len(report.results),
        "server_errors_5xx": len(report.server_errors),
        "unexpected_failures": len(report.unexpected_failures),
        "phase_counts": phase_counts,
        "skip_ugr": skip_ugr,
        "health_preflight": status,
        "health_postflight": status2,
        "server_still_healthy": status2 == 200,
    }

    print("\n=== FEDERATION CHAOS SUMMARY ===")
    print(json.dumps(summary, indent=2))
    if report.server_errors:
        print("\n!!! SERVER ERRORS (5xx) !!!")
        for r in report.server_errors[:20]:
            print(f"  {r.name} -> {r.status} {r.note}")
    if report.unexpected_failures:
        print("\n!!! UNEXPECTED FAILURES (<500 but not expected) !!!")
        for r in report.unexpected_failures[:20]:
            print(f"  {r.name} -> {r.status} {r.note}")

    out = write_chaos_report(report, summary, filename="federation_chaos_report.json")
    print(f"\nReport: {out}")
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--base",
        default=None,
        help="Override AAIS_STRESS_BASE (default http://127.0.0.1:8000)",
    )
    parser.add_argument(
        "--skip-ugr",
        action="store_true",
        help="Run civilizational phases only (skip UGR federation abuse)",
    )
    args = parser.parse_args(argv)
    if args.base:
        configure_base(args.base)

    summary = run_federation_chaos(skip_ugr=args.skip_ugr)
    if summary.get("fatal"):
        return 1
    if summary.get("server_errors_5xx", 0) > 0:
        return 1
    if not summary.get("server_still_healthy"):
        return 1
    if summary.get("unexpected_failures", 0) > 0:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
