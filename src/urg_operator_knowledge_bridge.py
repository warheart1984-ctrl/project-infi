"""Bridge proven URG discovery receipts into governed operator knowledge."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from src.rls.falsity_registry import FalsityRegistry
from src.rls.reasoning_graph import claim_fingerprint
from src.ugr.discovery.contribution_store import ContributionDiscoveryStore
from src.ugr.discovery.standing import (
    EpistemicState,
    build_epistemic_envelope,
    epistemic_from_receipt,
    is_library_admitted_epistemic,
    is_operator_promotable,
    standing_from_receipt,
)

PROMOTION_LEDGER_FILENAME = "urg_operator_promotions.jsonl"
DEFAULT_ENTRY_LIMIT = 8
DEFAULT_PROMPT_CHAR_BUDGET = 3200


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _default_runtime_dir() -> Path:
    configured = os.getenv("AAIS_RUNTIME_DIR")
    if configured:
        return Path(configured).expanduser()
    return Path(__file__).resolve().parents[1] / ".runtime"


def promotion_ledger_path(runtime_dir: str | Path | None = None) -> Path:
    root = Path(runtime_dir or _default_runtime_dir())
    return root / PROMOTION_LEDGER_FILENAME


def _read_promotion_rows(runtime_dir: str | Path | None = None) -> list[dict[str, Any]]:
    path = promotion_ledger_path(runtime_dir)
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return rows


def is_already_promoted(
    contribution_id: str,
    *,
    operator_id: str | None = None,
    runtime_dir: str | Path | None = None,
) -> bool:
    cid = str(contribution_id or "").strip()
    if not cid:
        return False
    op = str(operator_id or "").strip()
    for row in reversed(_read_promotion_rows(runtime_dir)):
        if str(row.get("contribution_id") or "").strip() != cid:
            continue
        if op and str(row.get("operator_id") or "").strip() not in {"", op}:
            continue
        if str(row.get("status") or "promoted") == "promoted":
            return True
    return False


def _entry_title(receipt: dict[str, Any], catalog_row: dict[str, Any] | None = None) -> str:
    payload = dict(receipt.get("payload") or {})
    proof = dict(receipt.get("proof") or {})
    for candidate in (
        payload.get("title"),
        payload.get("role"),
        payload.get("gene"),
        proof.get("title"),
        (catalog_row or {}).get("summary"),
    ):
        cleaned = " ".join(str(candidate or "").split()).strip()
        if cleaned:
            return cleaned
    return str(receipt.get("contribution_id") or receipt.get("subsystem_id") or "urg contribution")


def _entry_summary(receipt: dict[str, Any], catalog_row: dict[str, Any] | None = None) -> str:
    payload = dict(receipt.get("payload") or {})
    for candidate in (
        payload.get("proof_path"),
        payload.get("source_document_path"),
        payload.get("workflow_id"),
        (catalog_row or {}).get("summary"),
    ):
        cleaned = " ".join(str(candidate or "").split()).strip()
        if cleaned:
            return cleaned
    return _entry_title(receipt, catalog_row)


def _bounded_entries(
    entries: list[dict[str, Any]],
    *,
    char_budget: int = DEFAULT_PROMPT_CHAR_BUDGET,
) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    used = 0
    for entry in entries:
        line = f"{entry.get('contribution_id')}: {entry.get('title')} ({entry.get('epistemic_state')})"
        if used and used + len(line) > char_budget:
            break
        selected.append(entry)
        used += len(line) + 1
    return selected


def load_urg_library_snapshot(
    *,
    tenant_id: str = "global",
    runtime_dir: str | Path | None = None,
    limit: int = DEFAULT_ENTRY_LIMIT,
    query: str | None = None,
    epistemic_filter: set[str] | None = None,
) -> dict[str, Any]:
    store = ContributionDiscoveryStore(runtime_dir=runtime_dir, tenant_id=tenant_id)
    query_text = " ".join(str(query or "").lower().split())
    allowed = epistemic_filter or {
        EpistemicState.PENDING.value,
        EpistemicState.PROVEN.value,
    }

    catalog_rows = store.list_catalog(limit=max(int(limit or DEFAULT_ENTRY_LIMIT) * 4, 20))
    entries: list[dict[str, Any]] = []
    for catalog_row in reversed(catalog_rows):
        cid = str(catalog_row.get("contribution_id") or catalog_row.get("subsystem_id") or "").strip()
        if not cid:
            continue
        receipt = store.get_by_contribution_id(cid)
        if not receipt:
            continue
        ep = epistemic_from_receipt(receipt)
        if ep.value not in allowed or not is_library_admitted_epistemic(ep):
            continue
        title = _entry_title(receipt, catalog_row)
        summary = _entry_summary(receipt, catalog_row)
        haystack = f"{title} {summary} {cid}".lower()
        if query_text and query_text not in haystack:
            continue
        payload = dict(receipt.get("payload") or {})
        entries.append(
            {
                "contribution_id": cid,
                "contribution_type": receipt.get("contribution_type") or catalog_row.get("contribution_type"),
                "title": title,
                "summary": summary,
                "epistemic_state": ep.value,
                "claim_label": str(payload.get("claim_label") or ""),
                "standing": int(standing_from_receipt(receipt)),
                "operator_id": receipt.get("operator_id") or catalog_row.get("operator_id"),
                "promoted_to_operator": is_already_promoted(cid, runtime_dir=runtime_dir),
            }
        )

    entries.sort(
        key=lambda row: (
            0 if row.get("epistemic_state") == EpistemicState.PROVEN.value else 1,
            str(row.get("title") or ""),
        )
    )
    bounded = _bounded_entries(entries[: max(int(limit or DEFAULT_ENTRY_LIMIT), 1)])
    return {
        "tenant_id": tenant_id,
        "entry_count": len(bounded),
        "entries": bounded,
        "query": query_text or None,
    }


def build_urg_library_prompt_block(snapshot: dict[str, Any] | None) -> str:
    payload = dict(snapshot or {})
    entries = list(payload.get("entries") or [])
    if not entries:
        return ""
    lines = [
        "URG library knowledge is attached for this turn.",
        "Treat proven entries as governed operator truth; pending entries remain advisory.",
        f"Loaded {len(entries)} URG catalog entries.",
    ]
    for entry in entries:
        lines.extend(
            [
                "",
                f"- [{entry.get('contribution_id')}] {entry.get('title')}",
                f"  epistemic_state: {entry.get('epistemic_state')}",
                f"  summary: {entry.get('summary')}",
            ]
        )
    return "\n".join(lines).strip()


def build_urg_library_context(
    *,
    tenant_id: str = "global",
    runtime_dir: str | Path | None = None,
    limit: int = DEFAULT_ENTRY_LIMIT,
    query: str | None = None,
) -> dict[str, Any]:
    snapshot = load_urg_library_snapshot(
        tenant_id=tenant_id,
        runtime_dir=runtime_dir,
        limit=limit,
        query=query,
    )
    prompt_block = build_urg_library_prompt_block(snapshot)
    return {
        "tenant_id": tenant_id,
        "entries": snapshot.get("entries") or [],
        "entry_count": snapshot.get("entry_count") or 0,
        "query": snapshot.get("query"),
        "summary": (
            f"Loaded {snapshot.get('entry_count') or 0} URG library entries."
            if snapshot.get("entry_count")
            else "No URG library entries matched."
        ),
        "prompt_block": prompt_block,
    }


def _append_promotion_record(
    record: dict[str, Any],
    *,
    runtime_dir: str | Path | None = None,
) -> None:
    path = promotion_ledger_path(runtime_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True, default=str) + "\n")


def promote_from_receipt(
    receipt: dict[str, Any],
    *,
    operator_id: str,
    tenant_id: str = "global",
    runtime_dir: str | Path | None = None,
    memory_enforcer=None,
    falsity_registry: FalsityRegistry | None = None,
    record_odl: bool = True,
) -> dict[str, Any]:
    receipt_obj = dict(receipt or {})
    contribution_id = str(
        receipt_obj.get("contribution_id") or receipt_obj.get("subsystem_id") or ""
    ).strip()
    if not contribution_id:
        return {"ok": False, "skipped": True, "reason": "missing_contribution_id"}

    op_id = str(operator_id or receipt_obj.get("operator_id") or "").strip()
    if not op_id:
        return {"ok": False, "skipped": True, "reason": "missing_operator_id"}

    if is_already_promoted(contribution_id, operator_id=op_id, runtime_dir=runtime_dir):
        return {
            "ok": True,
            "skipped": True,
            "idempotent": True,
            "contribution_id": contribution_id,
            "operator_id": op_id,
        }

    ep = epistemic_from_receipt(receipt_obj)
    if ep == EpistemicState.REJECTED or not is_operator_promotable(ep):
        return {
            "ok": False,
            "skipped": True,
            "reason": "not_operator_promotable",
            "epistemic_state": ep.value,
            "contribution_id": contribution_id,
        }

    payload = dict(receipt_obj.get("payload") or {})
    title = _entry_title(receipt_obj)
    summary = _entry_summary(receipt_obj)
    fingerprint = str(payload.get("falsity_fingerprint") or claim_fingerprint(title)).strip()
    if falsity_registry is None:
        root = Path(runtime_dir or _default_runtime_dir())
        falsity_registry = FalsityRegistry(path=root / "rls_falsity_registry.jsonl")
    registry = falsity_registry
    if registry.is_resurrection_blocked(fingerprint):
        return {
            "ok": False,
            "skipped": True,
            "reason": "resurrection_blocked",
            "falsity_fingerprint": fingerprint,
            "contribution_id": contribution_id,
        }

    memory_text = " ".join(
        part
        for part in (
            f"URG proven contribution {contribution_id}.",
            title,
            summary,
        )
        if part
    ).strip()

    memory_id = None
    if memory_enforcer is None:
        try:
            from src import jarvis_operator

            memory_enforcer = jarvis_operator.memory_enforcer
        except Exception:
            memory_enforcer = None

    if memory_enforcer is not None:
        try:
            saved = memory_enforcer.add_memory(
                memory_text,
                tags=["urg", "proven", contribution_id],
                source="urg_library",
                category="urg_proven",
                truth_status="canonical",
                why=f"Auto-promoted from URG proof-of-discovery receipt ({contribution_id}).",
            )
            memory_id = getattr(saved, "id", None) or (saved.get("id") if isinstance(saved, dict) else None)
        except Exception as exc:
            return {
                "ok": False,
                "skipped": True,
                "reason": "memory_write_failed",
                "error": str(exc),
                "contribution_id": contribution_id,
            }

    promotion_event_id = f"urg-promo-{uuid4().hex[:12]}"
    envelope = build_epistemic_envelope(
        standing_from_receipt(receipt_obj),
        claim_label=str(payload.get("claim_label") or ""),
        contribution_id=contribution_id,
        promoted_to_operator=True,
        promotion_event_id=promotion_event_id,
        falsity_fingerprint=fingerprint or None,
    )
    promotion_record = {
        "status": "promoted",
        "promotion_event_id": promotion_event_id,
        "contribution_id": contribution_id,
        "operator_id": op_id,
        "tenant_id": tenant_id,
        "memory_id": memory_id,
        "recorded_at": _utc_now_iso(),
        "epistemic_envelope": envelope,
    }
    _append_promotion_record(promotion_record, runtime_dir=runtime_dir)

    odl_event = None
    if record_odl:
        try:
            from src.operator_decision_ledger import append_urg_knowledge_promotion_event

            odl_event = append_urg_knowledge_promotion_event(
                contribution_id=contribution_id,
                operator_id=op_id,
                tenant_id=tenant_id,
                memory_id=memory_id,
                promotion_event_id=promotion_event_id,
                epistemic_state=ep.value,
            )
        except Exception:
            odl_event = None

    return {
        "ok": True,
        "promoted": True,
        "contribution_id": contribution_id,
        "operator_id": op_id,
        "memory_id": memory_id,
        "promotion_event_id": promotion_event_id,
        "epistemic_state": ep.value,
        "odl_event": odl_event,
    }
