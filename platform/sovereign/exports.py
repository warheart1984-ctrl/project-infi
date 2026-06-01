"""Compliance CSV exports (v29)."""

from __future__ import annotations

import csv
from io import StringIO
from typing import Any

from platform.store import PlatformStore


def export_audit_csv(*, store: PlatformStore, org_id: str, limit: int = 500) -> str:
    rows = store.list_audit(org_id=org_id, limit=limit)
    buffer = StringIO()
    if not rows:
        return "org_id,action,principal_id,job_id\n"
    fieldnames = sorted({k for r in rows for k in r.keys()})
    writer = csv.DictWriter(buffer, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()
    for row in rows:
        writer.writerow(row)
    return buffer.getvalue()


def export_attestations_csv(
    *,
    store: PlatformStore,
    org_id: str,
    day_from: str = "",
    day_to: str = "",
) -> str:
    buffer = StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["job_id", "runner_id", "result_hash", "region", "signed_at", "signature_alg"])
    for job in store.list_jobs(org_id=org_id):
        for att in store.list_attestations(job_id=str(job["job_id"])):
            signed = str(att.get("signed_at") or "")
            if day_from and signed[:10] < day_from[:10]:
                continue
            if day_to and signed[:10] > day_to[:10]:
                continue
            writer.writerow(
                [
                    att.get("job_id"),
                    att.get("runner_id"),
                    att.get("result_hash"),
                    att.get("region"),
                    signed,
                    att.get("signature_alg"),
                ]
            )
    return buffer.getvalue()


def export_usage_csv_range(
    *,
    store: PlatformStore,
    org_id: str,
    day_from: str = "",
    day_to: str = "",
) -> str:
    from platform.billing.aggregator import export_usage_csv

    month = (day_from or day_to or "")[:7] or "2026-01"
    text = export_usage_csv(store=store, org_id=org_id, month=month)
    if not day_from and not day_to:
        return text
    lines = text.splitlines()
    if not lines:
        return text
    header = lines[0]
    out = [header]
    for line in lines[1:]:
        parts = line.split(",")
        if len(parts) < 2:
            continue
        day = parts[1]
        if day_from and day < day_from:
            continue
        if day_to and day > day_to:
            continue
        out.append(line)
    return "\n".join(out) + "\n"
