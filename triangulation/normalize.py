"""Normalize subsystem ledger records into triangulation claims."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Literal

SourceName = Literal["mechanic", "scorpion", "slingshot"]


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        rows.append(json.loads(line))
    return rows


def normalize_mechanic_claims(
    *,
    ledger_path: Path,
    case_id: str,
) -> list[dict[str, Any]]:
    claims: list[dict[str, Any]] = []
    for row in _load_jsonl(ledger_path):
        if str(row.get("case_id") or "") != case_id:
            continue
        claims.append(
            {
                "claim_id": str(row.get("record_id") or row.get("code") or "unknown"),
                "source": "mechanic",
                "invariant_id": str(row.get("invariant_id") or row.get("code") or ""),
                "claim_label": row.get("claim_label") or row.get("claim_status") or "asserted",
                "why_short": str(row.get("drift_summary") or row.get("reason") or "")[:500],
                "proof_links": list(row.get("evidence_refs") or []),
                "recorded_at_utc": row.get("recorded_at_utc"),
            }
        )
    return claims


def normalize_scorpion_claims(
    *,
    ledger_path: Path,
    case_id: str,
) -> list[dict[str, Any]]:
    claims: list[dict[str, Any]] = []
    for row in _load_jsonl(ledger_path):
        if str(row.get("case_id") or "") != case_id:
            continue
        claims.append(
            {
                "claim_id": str(row.get("record_id") or row.get("invariant_id") or "unknown"),
                "source": "scorpion",
                "invariant_id": str(row.get("invariant_id") or ""),
                "claim_label": row.get("claim_label") or row.get("claim_status") or "asserted",
                "why_short": str(row.get("drift_summary") or row.get("reason") or "")[:500],
                "proof_links": list(row.get("evidence_refs") or []),
                "recorded_at_utc": row.get("recorded_at_utc"),
            }
        )
    return claims


def normalize_slingshot_claims(
    *,
    frame_path: Path,
    ledger_path: Path | None = None,
    case_id: str,
) -> list[dict[str, Any]]:
    claims: list[dict[str, Any]] = []
    if frame_path.is_file():
        frame = json.loads(frame_path.read_text(encoding="utf-8"))
        if str(frame.get("case_id") or "") == case_id:
            claims.append(
                {
                    "claim_id": f"slingshot-frame-{case_id}",
                    "source": "slingshot",
                    "invariant_id": "slingshot_frame",
                    "claim_label": frame.get("claim_label") or "asserted",
                    "why_short": (
                        f"launch_blocked={frame.get('launch_blocked')} "
                        f"drift_count={frame.get('drift_count')}"
                    )[:500],
                    "proof_links": [str(frame_path)],
                    "recorded_at_utc": frame.get("created_at_utc"),
                    "launch_blocked": bool(frame.get("launch_blocked")),
                }
            )
    if ledger_path and ledger_path.is_file():
        for row in _load_jsonl(ledger_path):
            if str(row.get("case_id") or "") not in {"", case_id}:
                continue
            claims.append(
                {
                    "claim_id": str(row.get("event_id") or row.get("record_id") or "sl-event"),
                    "source": "slingshot",
                    "invariant_id": str(row.get("event") or "slingshot_event"),
                    "claim_label": row.get("claim_label") or "asserted",
                    "why_short": str(row.get("summary") or row.get("event") or "")[:500],
                    "proof_links": [],
                    "recorded_at_utc": row.get("recorded_at_utc"),
                }
            )
    return claims
