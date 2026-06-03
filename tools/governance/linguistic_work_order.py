#!/usr/bin/env python3
"""CLI — linguistic governance work orders (Wave 14, Wave 17 ops)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.governance_organs.linguistic_governance_queue_engine import (  # noqa: E402
    load_governance_queue,
)
from src.governance_organs.linguistic_governance_work_order_engine import (  # noqa: E402
    complete_top_work_orders,
    export_work_orders_json,
    load_all_work_orders,
    render_governance_queue_markdown,
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
    parser.add_argument("--ack-top", type=int, default=0, metavar="N")
    parser.add_argument("--complete-top", type=int, default=0, metavar="N")
    parser.add_argument("--export-json", type=str, default="", metavar="PATH")
    parser.add_argument("--export-markdown", type=str, default="", metavar="PATH")
    args = parser.parse_args()

    if args.complete_top > 0:
        genes = complete_top_work_orders(_ROOT, top_n=args.complete_top)
        print(f"completed {len(genes)} work order(s)")
        return 0

    if args.export_json:
        payload = export_work_orders_json(_ROOT)
        out = Path(args.export_json)
        if not out.is_absolute():
            out = _ROOT / out
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        print(f"wrote {out}")
        return 0

    if args.export_markdown:
        md = render_governance_queue_markdown(_ROOT)
        out = Path(args.export_markdown)
        if not out.is_absolute():
            out = _ROOT / out
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(md, encoding="utf-8")
        print(f"wrote {out}")
        return 0

    if args.ack_top > 0:
        sync_work_orders_from_queue(_ROOT)
        queue = load_governance_queue(_ROOT)
        genes = [
            item["gene"]
            for item in (queue.get("items") or [])[: args.ack_top]
            if item.get("gene")
        ]
        for gene in genes:
            set_work_order_status(gene, "acknowledged", root=_ROOT)
        print(f"acknowledged {len(genes)} work order(s)")
        return 0

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
