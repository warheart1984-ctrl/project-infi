#!/usr/bin/env python3
"""Generate linguistic remediation playbooks from drift scores."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.governance_organs.linguistic_remediation_engine import write_playbook  # noqa: E402
from tools.linguistic_drift_predictor import score_gene  # noqa: E402
from tools.linguistic_genome_lib import list_all_genes, load_json  # noqa: E402

BAND_ORDER = {"high": 3, "medium": 2, "low": 1}


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate remediation playbooks")
    parser.add_argument("--gene", help="Single gene")
    parser.add_argument("--min-band", choices=["low", "medium", "high"], default="medium")
    parser.add_argument("--top", type=int, default=20)
    parser.add_argument("--write-deltas", action="store_true", help="Write draft MP-LING JSON")
    args = parser.parse_args()

    root = _ROOT
    genes = [args.gene] if args.gene else list_all_genes(root)
    scored = [score_gene(g, root) for g in genes]
    min_rank = BAND_ORDER[args.min_band]
    scored = [s for s in scored if BAND_ORDER.get(s.band, 0) >= min_rank]
    scored.sort(key=lambda s: (-s.drift_risk, s.gene))
    if not args.gene:
        scored = scored[: args.top]

    written = 0
    for s in scored:
        path = write_playbook(s, root, write_delta_files=args.write_deltas)
        print(f"Wrote {path.relative_to(root)} ({s.band}, risk={s.drift_risk})")
        written += 1

    print(f"generate-linguistic-remediations: {written} playbook(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
