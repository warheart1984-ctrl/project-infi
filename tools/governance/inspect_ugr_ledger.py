#!/usr/bin/env python3
"""CLI for UGR ledger inspection — duplicates, balance replay, registry drift."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from src.ugr.governance.ledger_inspection import inspect_ugr_ledger


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect UGR reward and discovery ledgers")
    parser.add_argument(
        "--runtime-dir",
        default="",
        help="AAIS runtime root (default: AAIS_RUNTIME_DIR or .runtime)",
    )
    parser.add_argument("--tenant-id", default="global", help="Tenant to inspect")
    parser.add_argument(
        "--ledger-path",
        default="",
        help="Override discovery-pods.jsonl path",
    )
    parser.add_argument(
        "--registry-path",
        default="",
        help="Override deploy/ugr/discovery-pods.json path",
    )
    parser.add_argument("--json", action="store_true", help="Emit full JSON report")
    args = parser.parse_args()

    report = inspect_ugr_ledger(
        runtime_dir=args.runtime_dir or None,
        tenant_id=args.tenant_id,
        ledger_path=args.ledger_path or None,
        registry_path=args.registry_path or None,
    )

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        status = "OK" if report.get("ok") else "FAIL"
        print(f"UGR ledger inspection: {status} (tenant={report.get('tenant_id')})")
        rewards = report.get("rewards") or {}
        balances = report.get("balances") or {}
        pods = report.get("discovery_pods") or {}
        contributions = report.get("contributions") or {}
        print(
            f"  rewards: {rewards.get('event_count', 0)} events, "
            f"{rewards.get('library_pattern_match_count', 0)} library_pattern_matched"
        )
        print(f"  balances: {balances.get('operator_count', 0)} operators replay-checked")
        print(
            f"  discovery_pods: ledger={pods.get('ledger_pod_count', 0)} "
            f"registry={pods.get('registry_pod_count', 0)}"
        )
        print(
            f"  contributions: {contributions.get('discovery_count', 0)} discoveries, "
            f"{contributions.get('unique_contribution_ids', 0)} unique ids"
        )
        for issue in report.get("issues") or []:
            print(f"  ! {issue}")

    return 0 if report.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
