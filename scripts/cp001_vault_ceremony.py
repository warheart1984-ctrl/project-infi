#!/usr/bin/env python3
"""
CP-001 Vault Ceremony — Bone King continuity proof sealed as sovereign artifact.

Runs AVCP-1.0:
  Package → Invariants → Reproduction → D-3 Seal → Vault Entry → Lineage → Announce
"""

from __future__ import annotations

import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from src.cori.vault.avcp import run_avcp_ceremony  # noqa: E402
from src.cori.vault.store import VaultStorage  # noqa: E402


def main() -> int:
    print("=== CONTINUITY PROOF #001 — AVCP-1.0 CEREMONY ===")

    result = run_avcp_ceremony(observer="Observer-01")
    VaultStorage().persist_ceremony(
        result.package,
        result.vault_entry,
        result.seal_record,
        result.lineage_registration,
    )

    print(f"[1] Package: {result.package.id} hash={result.package.canonical_hash[:16]}...")
    print(f"[2] VaultEntry: {result.vault_entry.id} status={result.vault_entry.status}")
    print(f"[3] D-3 Seal: {result.seal_record.id} seal={result.seal_record.seal_id}")
    print(f"[4] Lineage: {result.lineage_registration.id} root={result.lineage_registration.lineage_root_id}")
    print(f"[5] Announcement: {result.announcement.message}")

    log = result.reproduction_log[0]
    print(f"\nReproduction ({log.observer}): {log.result}")
    print(f"  {log.notes}")

    print("\n=== RESULT: Bone King chain is a permanent continuity artifact ===")
    print(f'VERIFIED FACT: "{result.package.artifacts.derived_claim.summary}"')
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print("CP-001 vault ceremony failed:", exc, file=sys.stderr)
        raise SystemExit(1) from exc
