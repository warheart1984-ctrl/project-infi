"""Background tempering dry-run — mine rail ledger for hot paths (Phase 4)."""

from __future__ import annotations

import argparse
import json
import os
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.cloud_forge.ledger import RailDecisionLedger


DEFAULT_LEDGER = (
    Path(__file__).resolve().parents[2]
    / "docs"
    / "proof"
    / "cloud-forge"
    / "rail-decisions.jsonl"
)
DEFAULT_OUTPUT = (
    Path(__file__).resolve().parents[2]
    / "ci-artifacts"
    / "cloud-forge-tempering-report.json"
)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def run_tempering_dry_run(
    *,
    ledger_path: str | Path | None = None,
    limit: int = 2000,
) -> dict[str, Any]:
    """
    Aggregate rail-decisions JSONL; suggest hot domains (no live mutation).
    """
    if os.environ.get("CLOUD_FORGE_TEMPERING_SKIP", "").strip().lower() in {"1", "true", "yes"}:
        return {
            "skipped": True,
            "reason": "CLOUD_FORGE_TEMPERING_SKIP",
            "claim_status": "asserted",
            "generated_at": _utc_now_iso(),
        }

    ledger = RailDecisionLedger(ledger_path or DEFAULT_LEDGER)
    records = ledger.read_records(limit=limit)

    rail_counts: Counter[str] = Counter()
    domain_counts: Counter[str] = Counter()
    express_by_domain: Counter[str] = Counter()

    for row in records:
        decision = row.get("rail_decision") or {}
        plan = row.get("cognition_plan") or {}
        rail = str(decision.get("rail") or "UNKNOWN")
        rail_counts[rail] += 1

        domain = (
            (row.get("task_snapshot") or {}).get("domain")
            or plan.get("domain_template")
            or (plan.get("template") or {}).get("template_id")
            or "unknown"
        )
        domain_counts[str(domain)] += 1
        if rail == "EXPRESS":
            express_by_domain[str(domain)] += 1

    domains_ranked = [
        {"domain": d, "count": c, "express_count": express_by_domain.get(d, 0)}
        for d, c in domain_counts.most_common(20)
    ]
    express_candidates = [
        d["domain"]
        for d in domains_ranked
        if d["express_count"] >= 2 and d["domain"] != "unknown"
    ]

    return {
        "skipped": False,
        "dry_run": True,
        "claim_status": "asserted",
        "generated_at": _utc_now_iso(),
        "record_count": len(records),
        "rail_counts": dict(rail_counts),
        "domains_ranked": domains_ranked,
        "express_candidates": express_candidates,
        "recommendations": [
            "Review express_candidates for L2 pre-bake eligibility.",
            "Do not auto-promote; submit COLLECTIVE_PATTERN_LEDGER verification per candidate.",
        ],
    }


def write_tempering_report(report: dict[str, Any], output_path: str | Path) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Cloud Forge tempering dry-run")
    parser.add_argument("--dry-run", action="store_true", default=True)
    parser.add_argument("--ledger-path", default=str(DEFAULT_LEDGER))
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    args = parser.parse_args(argv)

    report = run_tempering_dry_run(ledger_path=args.ledger_path)
    out = write_tempering_report(report, args.output)
    print(json.dumps({"ok": True, "output": str(out), "record_count": report.get("record_count", 0)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
