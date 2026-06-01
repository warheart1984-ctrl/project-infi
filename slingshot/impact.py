"""Phase 4 — Impact: governed catch-zone receipts and ledger."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from uuid import uuid4

from slingshot.common import (
    DEFAULT_MECHANIC_ROOT,
    DEFAULT_SLINGSHOT_ROOT,
    IMPACT_VERSION,
    frame_path,
    hash_text,
    json_stable,
    ledger_path,
    mechanic_case_dir,
    packet_path,
    receipts_dir,
    sha256_file,
)


def _hash_manifest(case_id: str, *, slingshot_root: Path, mechanic_root: Path) -> dict[str, str]:
    manifest: dict[str, str] = {}
    for label, path in (
        ("frame", frame_path(case_id, runtime_root=slingshot_root)),
        ("packet", packet_path(case_id, runtime_root=slingshot_root)),
        ("mechanic_scan", mechanic_case_dir(case_id, runtime_root=mechanic_root) / "mechanic_scan.v1.json"),
        (
            "runtime_profile",
            mechanic_case_dir(case_id, runtime_root=mechanic_root) / "MECHANIC_RUNTIME_PROFILE.json",
        ),
    ):
        if path.is_file():
            manifest[label] = sha256_file(path)
    return manifest


def build_impact_receipt(
    *,
    case_id: str,
    turn_id: str,
    user_message: str,
    assistant_reply: str,
    midflight_report: dict[str, Any],
    session_metadata: dict[str, Any] | None = None,
    compose_mode_used: str = "fast",
    cortex_fast_path: bool = True,
    slingshot_root: Path | None = None,
    mechanic_root: Path | None = None,
) -> dict[str, Any]:
    shot_root = slingshot_root or DEFAULT_SLINGSHOT_ROOT
    mech_root = mechanic_root or DEFAULT_MECHANIC_ROOT
    metadata = dict(session_metadata or {})
    receipt: dict[str, Any] = {
        "receipt_version": IMPACT_VERSION,
        "case_id": case_id,
        "turn_id": turn_id,
        "impact_status": str(midflight_report.get("impact_status") or "clean"),
        "user_message_preview": (user_message or "")[:240],
        "assistant_reply_preview": (assistant_reply or "")[:240],
        "turn_boundary_before": metadata.get("turn_boundary_before"),
        "turn_boundary_after": metadata.get("turn_boundary_after"),
        "stage2_metrics": midflight_report.get("stage2_metrics"),
        "drift_events": list(midflight_report.get("drift_events") or []),
        "compose_mode_used": compose_mode_used,
        "cortex_fast_path": cortex_fast_path,
        "hash_manifest": _hash_manifest(case_id, slingshot_root=shot_root, mechanic_root=mech_root),
        "claim_label": "asserted",
    }
    receipt["receipt_hash"] = hash_text(
        json_stable({k: v for k, v in receipt.items() if k != "receipt_hash"})
    )
    return receipt


def persist_impact_receipt(receipt: dict[str, Any], *, runtime_root: Path | None = None) -> Path:
    case_id = str(receipt.get("case_id") or "")
    turn_id = str(receipt.get("turn_id") or uuid4().hex[:12])
    root = runtime_root or DEFAULT_SLINGSHOT_ROOT
    out_dir = receipts_dir(case_id, runtime_root=root)
    out_dir.mkdir(parents=True, exist_ok=True)
    target = out_dir / f"{turn_id}.json"
    target.write_text(json.dumps(receipt, sort_keys=True, indent=2), encoding="utf-8")
    append_ledger_entry(
        case_id,
        {
            "event": "impact",
            "turn_id": turn_id,
            "impact_status": receipt.get("impact_status"),
            "receipt_hash": receipt.get("receipt_hash"),
        },
        runtime_root=root,
    )
    return target


def append_ledger_entry(case_id: str, record: dict[str, Any], *, runtime_root: Path | None = None) -> None:
    path = ledger_path(case_id, runtime_root=runtime_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True) + "\n")


def verify_slingshot_case(
    case_id: str,
    *,
    repo_path: str | Path | None = None,
    slingshot_root: Path | None = None,
    mechanic_root: Path | None = None,
) -> dict[str, Any]:
    """Verify frame/packet presence and optional Mechanic replay match."""
    shot_root = slingshot_root or DEFAULT_SLINGSHOT_ROOT
    mech_root = mechanic_root or DEFAULT_MECHANIC_ROOT
    frame_file = frame_path(case_id, runtime_root=shot_root)
    packet_file = packet_path(case_id, runtime_root=shot_root)
    ok = frame_file.is_file() and packet_file.is_file()
    replay: dict[str, Any] = {"matched": False, "claim_label": "asserted"}
    mech_dir = mechanic_case_dir(case_id, runtime_root=mech_root)
    if ok and repo_path and mech_dir.is_dir():
        from mechanic.hosted.worker import replay_scan

        replay = replay_scan(
            case_id=case_id,
            repo_path=repo_path,
            original_case_dir=mech_dir,
        )
    ledger = ledger_path(case_id, runtime_root=shot_root)
    receipt_count = len(list(receipts_dir(case_id, runtime_root=shot_root).glob("*.json")))
    return {
        "mode": "verify",
        "case_id": case_id,
        "ok": ok and bool(replay.get("matched", True) if repo_path else True),
        "frame_present": frame_file.is_file(),
        "packet_present": packet_file.is_file(),
        "receipt_count": receipt_count,
        "ledger_entries": sum(1 for _ in ledger.open(encoding="utf-8")) if ledger.is_file() else 0,
        "replay": replay,
        "claim_label": "proven" if ok and replay.get("matched") else "asserted",
    }
