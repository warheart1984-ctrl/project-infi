"""Receipt and Merkle verification for temporal replay."""

from __future__ import annotations

from typing import Any

from src.temporal_replay.law_pin import events_at_or_before, parse_at_timestamp
from src.ugr.mission.ledger_merkle import compute_ledger_merkle_root


def verify_replay(
    *,
    subject_type: str,
    subject_id: str,
    events: list[dict[str, Any]],
    at: str | None = None,
    tenant_id: str | None = None,
) -> dict[str, Any]:
    at_iso = parse_at_timestamp(at)
    scoped = events_at_or_before(events, at_iso)
    report: dict[str, Any] = {
        "subject_type": subject_type,
        "subject_id": subject_id,
        "at": at_iso,
        "checks": [],
        "ok": True,
        "claim_label": "asserted",
    }

    if subject_type == "mission":
        _verify_mission(subject_id, scoped, report, tenant_id=tenant_id)
    else:
        report["checks"].append({"name": "subject_verify", "ok": True, "detail": "no_mission_receipt_checks"})

    hard_fails = [
        e for e in scoped if (e.get("invariant_flags") or {}).get("hard_fail")
    ]
    if hard_fails:
        report["checks"].append(
            {
                "name": "invariant_overlay",
                "ok": False,
                "detail": f"{len(hard_fails)} hard_fail events at or before T",
                "event_ids": [e.get("event_id") for e in hard_fails[:20]],
            }
        )
        report["ok"] = False

    if report["ok"] and all(c.get("ok") for c in report["checks"]):
        proven_checks = [c for c in report["checks"] if c.get("name") in {"ledger_root", "receipt_signatures"}]
        if proven_checks and all(c.get("ok") for c in proven_checks):
            report["claim_label"] = "proven"

    return report


def _verify_mission(
    mission_id: str,
    scoped: list[dict[str, Any]],
    report: dict[str, Any],
    *,
    tenant_id: str | None,
) -> None:
    from src.ugr.mission.mission_ledger import MissionLedger
    from src.ugr.mission.mission_receipt_store import MissionReceiptStore
    from src.ugr.mission.receipt_signing import verify_mission_receipt_v2

    ledger = MissionLedger(tenant_id=tenant_id)
    rows = ledger.list_for_mission(mission_id)
    at_iso = scoped[-1].get("timestamp_utc") if scoped else None
    if at_iso:
        rows = [r for r in rows if str(r.get("timestamp") or "") <= at_iso] or rows

    computed = compute_ledger_merkle_root(rows)
    store = MissionReceiptStore(tenant_id=tenant_id or ledger.tenant_id)
    record = store.get_receipt(mission_id, tenant_id=store.tenant_id)
    schema = dict((record or {}).get("mission_receipt_schema") or {})
    expected = str(schema.get("ledger_root") or "")

    root_ok = (not expected) or computed == expected
    report["checks"].append(
        {
            "name": "ledger_root",
            "ok": root_ok,
            "detail": "match" if root_ok else f"expected={expected} computed={computed}",
            "computed": computed,
            "expected": expected,
        }
    )
    if not root_ok:
        report["ok"] = False

    if schema:
        ok, reason = verify_mission_receipt_v2(
            schema,
            ledger_rows=rows,
        )
        report["checks"].append(
            {
                "name": "receipt_signatures",
                "ok": ok,
                "detail": reason,
            }
        )
        if not ok:
            report["ok"] = False
    else:
        report["checks"].append(
            {"name": "receipt_signatures", "ok": True, "detail": "no_stored_receipt"}
        )
