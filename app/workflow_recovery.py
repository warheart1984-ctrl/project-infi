from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Callable

from app.config import (
    WORKFLOW_MAX_RECOVERY_ATTEMPTS,
    WORKFLOW_QUEUE_STALE_SECONDS,
    WORKFLOW_SWEEPER_LIMIT,
)
from app.db import (
    begin_workflow_run_recovery,
    list_expired_running_workflow_runs,
    list_stale_workflow_runs,
    log_event,
    mark_workflow_run_recovery_enqueue_failed,
    mark_workflow_run_stale,
    now_iso,
)


def _parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _is_older_than(value: str | None, seconds: int) -> bool:
    parsed = _parse_iso(value)
    if not parsed:
        return True
    return parsed <= datetime.now(timezone.utc) - timedelta(seconds=seconds)


def sweep_workflow_runs(enqueue_recovery: Callable[[str, str], None]) -> dict:
    expired_before = now_iso()
    summary = {
        "stale": [],
        "recovering": [],
        "recovery_failed": [],
    }

    for run in list_expired_running_workflow_runs(expired_before, limit=WORKFLOW_SWEEPER_LIMIT):
        stale = mark_workflow_run_stale(
            run["id"],
            reason="worker heartbeat expired",
            expired_before=expired_before,
        )
        if not stale:
            continue
        summary["stale"].append(stale["id"])
        log_event(
            "workflow_run_stale",
            {
                "workflow_run_id": stale["id"],
                "workflow_id": stale["workflow_id"],
                "reason": stale.get("stale_reason") or "worker heartbeat expired",
            },
        )

    for run in list_stale_workflow_runs(limit=WORKFLOW_SWEEPER_LIMIT):
        output = run.get("output") or {}
        if run.get("recovery_state") == "enqueue_failed" and not _is_older_than(
            output.get("lastRecoveryFailureAt"),
            WORKFLOW_QUEUE_STALE_SECONDS,
        ):
            continue

        recovering = begin_workflow_run_recovery(
            run["id"],
            reason=run.get("stale_reason") or "worker heartbeat expired",
            max_recovery_attempts=WORKFLOW_MAX_RECOVERY_ATTEMPTS,
        )
        if not recovering:
            continue

        if recovering["status"] == "failed":
            summary["recovery_failed"].append(recovering["id"])
            log_event(
                "workflow_recovery_exhausted",
                {
                    "workflow_run_id": recovering["id"],
                    "workflow_id": recovering["workflow_id"],
                    "recovery_attempts": recovering.get("recovery_attempts"),
                },
            )
            continue

        summary["recovering"].append(recovering["id"])
        log_event(
            "workflow_run_recovering",
            {
                "workflow_run_id": recovering["id"],
                "workflow_id": recovering["workflow_id"],
                "recovery_attempts": recovering.get("recovery_attempts"),
            },
        )

        try:
            enqueue_recovery(recovering["id"], recovering["workflow_id"])
        except Exception as exc:
            mark_workflow_run_recovery_enqueue_failed(recovering["id"], str(exc))
            log_event(
                "workflow_recovery_enqueue_failed",
                {
                    "workflow_run_id": recovering["id"],
                    "workflow_id": recovering["workflow_id"],
                    "error": str(exc),
                },
            )

    return summary
