#!/usr/bin/env python3
"""10-minute RA-COS demo — trigger → governance → registry → ledger (SQLite)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from src.continuity.css2.governance import RecalibrationGovernanceEngine
from src.continuity.css2.lineage_report import (
    generate_lineage_report,
    generate_threshold_chart_spec,
)
from src.continuity.css2.models import RecalibrationLedger
from src.continuity.css2.registry import default_recalibration_rule, seed_css1_thresholds
from src.continuity.css2.threshold import SystemState, Threshold
from src.continuity.css2.threshold_store import RacosThresholdStore
from src.continuity.ra.ra_cos_loop import process_ra_cos_event

SAFETY_THRESHOLD = Threshold(
    id="T_safety_override_001",
    name="Safety override threshold",
    domain="Safety.core",
    metric="safety_violations_per_hour",
    comparator=">",
    value=0,
    intent="Any safety violation triggers immediate halt.",
    created_by="demo-seed",
    last_updated_by="demo-seed",
)


def seed_demo_thresholds() -> list[Threshold]:
    return [*seed_css1_thresholds(), SAFETY_THRESHOLD]


def _section(title: str) -> None:
    print()
    print(f"=== {title} ===")


def _show_investor(msg: str, audience: str) -> None:
    if audience in ("investor", "all"):
        print(f"[investor] {msg}")


def _show_technical(msg: str, audience: str) -> None:
    if audience in ("technical", "all"):
        print(f"[technical] {msg}")


def _show_governance(msg: str, audience: str) -> None:
    if audience in ("governance", "all"):
        print(f"[governance] {msg}")


def run_demo(*, db_path: Path, audience: str, lineage_out: Path | None) -> int:
    store = RacosThresholdStore(path=db_path)
    store.seed_from_list(seed_demo_thresholds())

    thresholds = store.load_thresholds()
    pt3 = next(t for t in thresholds if t.metric == "propagation_count")
    safety = next(t for t in thresholds if t.id == SAFETY_THRESHOLD.id)

    _section("Minute 0–2 — Seeded thresholds")
    _show_investor(
        f"Operational metric {pt3.metric}: current value {pt3.value}",
        audience,
    )
    _show_investor(
        f"Safety metric {safety.metric}: current value {safety.value} (rejection beat)",
        audience,
    )
    counts = store.count_rows()
    _show_technical(
        f"threshold id={pt3.id} comparator={pt3.comparator} value={pt3.value}; "
        f"rows thresholds={counts['thresholds']} versions={counts['threshold_versions']}",
        audience,
    )
    _show_governance(f"PT-3 intent: {pt3.intent}", audience)
    _show_governance(f"Safety intent: {safety.intent}", audience)

    ledger = RecalibrationLedger()
    engine = RecalibrationGovernanceEngine(ledger=ledger)
    state = SystemState(
        thresholds=store.load_thresholds(),
        recalibration_rule=default_recalibration_rule(),
    )
    before_value = pt3.value

    _section("Minute 2–4 — Trigger (late_intervention)")
    event = {"metric": pt3.metric, "domain": pt3.domain}
    validation = {"late_intervention": True}
    print(f"Event: {event}")
    print(f"Validation: {validation}")

    _section("Minute 4–6 — Governance + registry update")
    result = process_ra_cos_event(
        event,
        {},
        validation,
        state,
        governance=engine,
        store=store,
    )
    for trig in result.triggers:
        print(f"Trigger: {trig.reason} on {trig.threshold_id}")
    for rec in result.events:
        _show_investor(f"Decision: {rec.decision.upper()} — {rec.legitimacy_basis[:120]}", audience)
        _show_technical(
            f"event_id={rec.event_id} decision={rec.decision} audit_trail={rec.audit_trail}",
            audience,
        )
        _show_governance(f"Legitimacy: {rec.legitimacy_basis}", audience)
        for note in rec.audit_trail:
            _show_governance(f"Audit: {note}", audience)

    updated = store.get_threshold(pt3.id)
    assert updated is not None
    _section("Minute 6–8 — Registry after approval")
    _show_investor(f"{pt3.metric}: {before_value} → {updated.value}", audience)
    history = store.get_history(pt3.id)
    _show_technical(
        f"version rows: {[v.version for v in history]}",
        audience,
    )
    for v in history:
        _show_governance(
            f"v{v.version}: value={v.snapshot.value} rationale={v.delta_rationale}",
            audience,
        )

    _section("Minute 8–9 — Rejection beat (safety / CRK)")
    reject_result = process_ra_cos_event(
        {"metric": safety.metric, "domain": safety.domain},
        {},
        {"over_intervention_count": 5, "metric": safety.metric},
        SystemState(thresholds=store.load_thresholds(), recalibration_rule=default_recalibration_rule()),
        governance=engine,
        store=store,
    )
    safety_after = store.get_threshold(safety.id)
    assert safety_after is not None
    for rec in reject_result.events:
        print(f"Rejection event: {rec.decision} — {rec.legitimacy_basis}")
    print(f"Safety value unchanged: {safety_after.value} (still 0)")
    rejected = store.list_recalibration_events(decision="rejected", limit=5)
    _show_technical(f"rejected ledger rows: {len(rejected)}", audience)

    _section("Minute 9–10 — Lineage")
    history = store.get_history(pt3.id)
    report = generate_lineage_report(history)
    chart = generate_threshold_chart_spec(history)
    _show_investor("Every threshold change is attributable via version history and ledger events.", audience)
    _show_governance(report, audience)
    _show_technical(json.dumps(chart, indent=2), audience)
    if lineage_out is not None:
        lineage_out.write_text(report, encoding="utf-8")
        _show_technical(f"Wrote lineage report to {lineage_out}", audience)

    _section("Done")
    print("Story: detect → govern → registry update → audit trail — no silent drift.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="RA-COS 10-minute demo (SQLite-backed)")
    parser.add_argument(
        "--db",
        type=Path,
        default=Path("data/demo_ra_cos.sqlite3"),
        help="SQLite database path (default: data/demo_ra_cos.sqlite3)",
    )
    parser.add_argument(
        "--audience",
        choices=("all", "technical", "investor", "governance"),
        default="all",
        help="Output emphasis layer",
    )
    parser.add_argument(
        "--lineage-out",
        type=Path,
        default=None,
        help="Write markdown lineage report to this path",
    )
    args = parser.parse_args(argv)
    return run_demo(db_path=args.db, audience=args.audience, lineage_out=args.lineage_out)


if __name__ == "__main__":
    sys.exit(main())
