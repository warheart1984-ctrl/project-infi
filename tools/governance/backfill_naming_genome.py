#!/usr/bin/env python3
"""Backfill ssp.engineering_class, mythic_label, linguistic_version on all genomes."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from tools.linguistic_genome_lib import (  # noqa: E402
    load_aliases,
    load_json,
    resolve_linguistic_names,
)

GENOME_DIR = _ROOT / "governance" / "subsystem_genomes"


def backfill_genome(data: dict, aliases: dict) -> bool:
    identity = data.get("identity") or {}
    gene = identity.get("gene", "")
    if not gene:
        return False
    ssp = data.setdefault("ssp", {})
    changed = False
    eng, mythic = resolve_linguistic_names(gene, aliases)
    if eng and ssp.get("engineering_class") != eng:
        ssp["engineering_class"] = eng
        changed = True
    if mythic and ssp.get("mythic_label") != mythic:
        ssp["mythic_label"] = mythic
        changed = True
    if not ssp.get("linguistic_version"):
        ssp["linguistic_version"] = "1.0.0"
        changed = True
    return changed


def main() -> int:
    parser = argparse.ArgumentParser(description="Backfill naming genome SSP fields")
    parser.add_argument(
        "--write",
        action="store_true",
        help="Write changes to genome files (default dry-run)",
    )
    args = parser.parse_args()

    aliases = load_aliases(_ROOT)
    updated = 0
    scanned = 0

    for path in sorted(GENOME_DIR.glob("*.genome.v1.json")):
        scanned += 1
        data = load_json(path)
        if backfill_genome(data, aliases):
            updated += 1
            gene = (data.get("identity") or {}).get("gene", path.name)
            eng = (data.get("ssp") or {}).get("engineering_class", "")
            print(f"{'WRITE' if args.write else 'DRY'}: {gene} -> {eng}")
            if args.write:
                path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

    print(f"backfill: {updated}/{scanned} genome(s) {'written' if args.write else 'would update'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
