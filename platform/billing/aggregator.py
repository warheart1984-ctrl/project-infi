"""Daily usage rollups and CSV export."""

from __future__ import annotations

import csv
from datetime import datetime
from io import StringIO
from pathlib import Path
from typing import Any

from src.datetime_compat import UTC

from platform.store import PlatformStore


def record_marketplace_event(
    *,
    store: PlatformStore,
    org_id: str,
    event_type: str,
    listing_id: str = "",
) -> None:
    event: dict[str, Any] = {"day": datetime.now(UTC).date().isoformat()}
    if event_type == "install":
        event["marketplace_installs"] = 1
        if listing_id:
            event["listing_installs_by_id"] = {listing_id: 1}
    if event_type == "workflow_run":
        event["workflow_runs_from_listing"] = 1
    store.record_usage(org_id=org_id, event=event)
    from platform.ledger.hooks import ledger_usage

    ledger_usage(store=store, org_id=org_id, event=event)


def record_job_completion(*, store: PlatformStore, job: dict[str, Any]) -> None:
    org_id = str(job.get("org_id"))
    subsystem = str(job.get("subsystem"))
    event: dict[str, Any] = {
        "day": datetime.now(UTC).date().isoformat(),
        "jobs_count": 1,
        "estimated_cost": float(job.get("actual_cost") or job.get("cost_estimate") or 0),
    }
    if subsystem == "mechanic":
        event["mechanic_jobs"] = 1
    if subsystem == "slingshot":
        event["slingshot_jobs"] = 1
    store.record_usage(org_id=org_id, event=event)
    from platform.ledger.hooks import ledger_usage

    ledger_usage(store=store, org_id=org_id, event=event)


def export_usage_csv(*, store: PlatformStore, org_id: str, month: str) -> str:
    day_from = f"{month}-01"
    day_to = f"{month}-31"
    rows = store.list_usage(org_id=org_id, day_from=day_from, day_to=day_to)
    buffer = StringIO()
    writer = csv.DictWriter(
        buffer,
        fieldnames=[
            "org_id",
            "day",
            "jobs_count",
            "mechanic_jobs",
            "slingshot_jobs",
            "artifacts_count",
            "storage_bytes",
            "estimated_cost",
        ],
    )
    writer.writeheader()
    for row in rows:
        writer.writerow({k: row.get(k, "") for k in writer.fieldnames})
    return buffer.getvalue()


def write_usage_csv(*, store: PlatformStore, org_id: str, month: str, output: Path) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(export_usage_csv(store=store, org_id=org_id, month=month), encoding="utf-8")
    return output
