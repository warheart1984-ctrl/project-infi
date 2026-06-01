"""Run governed UGR ingestion from the CLI."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.ugr.ingestion.pipeline import GovernedIngestionPipeline


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Run UGR governed ingestion")
    parser.add_argument("--source", required=True, help="Source id from ingestion.sources.json")
    parser.add_argument("--dry-run", action="store_true", help="Propose without ledger writes")
    parser.add_argument("--config", default="", help="Override UGR_INGESTION_CONFIG path")
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    if args.config:
        import os

        os.environ["UGR_INGESTION_CONFIG"] = args.config
    pipeline = GovernedIngestionPipeline()
    result = pipeline.run_source(args.source, dry_run=args.dry_run)
    print(json.dumps(result.to_dict(), indent=2, default=str))
    return 0 if result.status in {"ok", "no_accepted_proposals", "quarantined"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
