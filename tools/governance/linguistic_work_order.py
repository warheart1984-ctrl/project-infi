#!/usr/bin/env python3
"""CLI — linguistic governance work orders (Wave 14)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.governance_organs.linguistic_governance_work_order_engine import (  # noqa: E402
    load_all_work_orders,
    set_work_order_status,
    sync_work_orders_from_queue,
    work_order_summary,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Linguistic governance work orders")
    parser.add_argument("--sync-from-queue", action="store_true")
    parser.add_argument("--summary", action="store_true")
    parser.add_argument("--gene", type=str, default="")
    parser.add_argument("--status", type=str, default="")
    parser.add_argument("--notes", type=str, default="")
    args = parser.parse_args()

    if args.sync_from_queue:
        paths = sync_work_orders_from_queue(_ROOT)
        print(f"synced {len(paths)} work order(s)")
        return 0

    if args.gene and args.status:
        wo = set_work_order_status(
            args.gene,
            args.status,
            root=_ROOT,
            operator_notes=args.notes or None,
        )
        print(json.dumps(wo, indent=2))
        return 0

    if args.summary:
        print(json.dumps(work_order_summary(_ROOT), indent=2))
        orders = load_all_work_orders(_ROOT)
        for gene, wo in sorted(orders.items(), key=lambda x: -x[1].get("urgency_score", 0))[:10]:
            print(f"  {gene}: {wo.get('status')} urgency={wo.get('urgency_score')}")
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
