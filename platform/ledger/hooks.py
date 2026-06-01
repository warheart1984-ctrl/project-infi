"""Ledger append hooks for operational writers (v47)."""

from __future__ import annotations

from typing import Any

from platform.ledger.writer import append_ledger_entry
from platform.store import PlatformStore


def ledger_audit(*, store: PlatformStore, record: dict[str, Any]) -> None:
    org_id = str(record.get("org_id") or "")
    if not org_id:
        return
    append_ledger_entry(
        store=store,
        org_id=org_id,
        kind="audit.event",
        payload={
            "action": record.get("action"),
            "principal_id": record.get("principal_id"),
            "job_id": record.get("job_id"),
        },
    )


def ledger_usage(*, store: PlatformStore, org_id: str, event: dict[str, Any]) -> None:
    if not org_id:
        return
    append_ledger_entry(
        store=store,
        org_id=org_id,
        kind="usage.rollup",
        payload={"day": event.get("day"), "event": {k: v for k, v in event.items() if k != "day"}},
    )


def ledger_attestation(*, store: PlatformStore, org_id: str, attestation: dict[str, Any]) -> None:
    if not org_id:
        return
    append_ledger_entry(
        store=store,
        org_id=org_id,
        kind="attestation.upsert",
        payload={
            "attestation_id": attestation.get("attestation_id"),
            "job_id": attestation.get("job_id"),
            "runner_id": attestation.get("runner_id"),
            "witness_id": attestation.get("witness_id"),
        },
    )


def ledger_webhook_delivery(*, store: PlatformStore, delivery: dict[str, Any]) -> None:
    org_id = str(delivery.get("org_id") or "")
    if not org_id:
        return
    append_ledger_entry(
        store=store,
        org_id=org_id,
        kind="webhook.delivery",
        payload={
            "delivery_id": delivery.get("delivery_id"),
            "event_type": delivery.get("event_type"),
            "status": delivery.get("status"),
        },
    )


def ledger_mesh_event(*, store: PlatformStore, org_id: str, event_type: str, payload: dict[str, Any]) -> None:
    append_ledger_entry(
        store=store,
        org_id=org_id,
        kind=f"mesh.{event_type}",
        payload=payload,
    )


def ledger_autopilot(*, store: PlatformStore, receipt: dict[str, Any]) -> None:
    append_ledger_entry(
        store=store,
        org_id=str(receipt.get("org_id") or ""),
        kind="mesh.autopilot",
        payload={"run_id": receipt.get("run_id"), "mode": receipt.get("mode"), "action_count": len(receipt.get("actions") or [])},
    )


def ledger_exchange(*, store: PlatformStore, org_id: str, kind: str, payload: dict[str, Any]) -> None:
    append_ledger_entry(store=store, org_id=org_id, kind=kind, payload=payload)
