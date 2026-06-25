#!/usr/bin/env python3
"""
Mission #001 Category B closure — FIRC-1.0 founder-independent reproduction.

Transitions:
  VERIFIED → COMPLETED
  Seal: D-3 (Founder-Independent Reproduction Achieved)
  Dossier: CLOSED
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from src.cori.vault.category_b import run_category_b_closure  # noqa: E402
from src.cori.vault.models import BK_CANONICAL_HASH, MISSION_001  # noqa: E402
from src.cori.vault.store import VaultStorage  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Register Category B vault closure")
    parser.add_argument("--observer", default="Bradley", help="Observer identity")
    parser.add_argument("--os", default="Ubuntu 24.04")
    parser.add_argument("--python", default="3.12")
    parser.add_argument("--json", action="store_true", help="Print closure record as JSON")
    args = parser.parse_args()

    print("=== MISSION #001 — CATEGORY B CLOSURE (FIRC-1.0) ===")

    result = run_category_b_closure(
        observer=args.observer,
        environment={
            "os": args.os,
            "python": args.python,
            "execution": "independent",
            "founder_infrastructure": "none",
        },
    )

    VaultStorage().persist_category_b_closure(
        result.package,
        result.vault_entry,
        result.seal_record,
        result.lineage_registration,
        result.observer_report,
        result.mission_completion,
        result.ceremony_completion,
        result.trust_boundary_update,
        result.mission_dossier,
    )

    summary = {
        "mission_id": MISSION_001,
        "state": "COMPLETED",
        "category": "B",
        "canonical_hash": BK_CANONICAL_HASH,
        "seal": "D-3",
        "observer": args.observer,
        "vault_entry": result.vault_entry.id,
        "observer_report_hash": result.observer_report.report_hash,
        "dossier_state": result.mission_dossier.state,
    }

    print(f"Mission:     {MISSION_001} → COMPLETED")
    print(f"Category:    B (Founder-Independent)")
    print(f"Observer:    {args.observer}")
    print(f"Canonical:   {BK_CANONICAL_HASH}")
    print(f"Seal:        D-3 (Founder-Independent Reproduction Achieved)")
    print(f"Vault:       {result.vault_entry.id} status={result.vault_entry.status}")
    print(f"Lineage:     {result.lineage_registration.lineage_root_id} registered")
    print(f"Dossier:     {result.mission_dossier.state}")

    if args.json:
        print(json.dumps(summary, indent=2))

    print("\n=== RESULT: Mission #001 closed — Category B reproduction registered ===")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print("Category B closure failed:", exc, file=sys.stderr)
        raise SystemExit(1) from exc
