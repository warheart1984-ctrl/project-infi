"""Linguistic governance work orders — Wave 14 operator execution posture."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.governance_organs._paths import repo_root
from src.governance_organs.linguistic_governance_queue_engine import load_governance_queue
from tools.linguistic_genome_lib import load_json

WORK_ORDER_VERSION = "linguistic_governance_work_order.v1"
VALID_STATUSES = frozenset({"pending", "acknowledged", "completed", "deferred"})


def work_orders_dir(root: Path | None = None) -> Path:
    root = root or repo_root()
    return root / "governance/linguistic_governance_work_orders"


def work_order_path(gene: str, root: Path | None = None) -> Path:
    safe = gene.replace("/", "_").replace("\\", "_")
    return work_orders_dir(root) / f"{safe}.v1.json"


def load_work_order(gene: str, root: Path | None = None) -> dict[str, Any] | None:
    path = work_order_path(gene, root)
    if path.is_file():
        return load_json(path)
    return None


def load_all_work_orders(root: Path | None = None) -> dict[str, dict[str, Any]]:
    root = root or repo_root()
    out: dict[str, dict[str, Any]] = {}
    wo_dir = work_orders_dir(root)
    if not wo_dir.is_dir():
        return out
    for path in wo_dir.glob("*.v1.json"):
        data = load_json(path)
        gene = data.get("gene") or path.stem.replace(".v1", "")
        if gene:
            out[gene] = data
    return out


def _new_work_order(
    item: dict[str, Any],
    *,
    existing: dict[str, Any] | None,
    now: str,
) -> dict[str, Any]:
    gene = item["gene"]
    status = "pending"
    operator_notes = ""
    if existing:
        status = existing.get("status", "pending")
        if status not in VALID_STATUSES:
            status = "pending"
        operator_notes = existing.get("operator_notes", "")
    return {
        "linguistic_governance_work_order_version": WORK_ORDER_VERSION,
        "gene": gene,
        "status": status,
        "urgency_score": item.get("urgency_score", 0),
        "queue_generated_at": item.get("queue_generated_at", now),
        "recommended_actions": item.get("recommended_actions") or [],
        "operator_notes": operator_notes,
        "updated_at": now,
    }


def sync_work_orders_from_queue(root: Path | None = None) -> list[Path]:
    """Sync work-order files from latest governance queue."""
    root = root or repo_root()
    queue = load_governance_queue(root)
    if not queue:
        return []
    wo_dir = work_orders_dir(root)
    wo_dir.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    q_at = queue.get("generated_at", now)
    existing = load_all_work_orders(root)
    written: list[Path] = []
    for item in queue.get("items") or []:
        gene = item.get("gene")
        if not gene:
            continue
        item = {**item, "queue_generated_at": q_at}
        payload = _new_work_order(item, existing=existing.get(gene), now=now)
        path = work_order_path(gene, root)
        path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        written.append(path)

    reg_path = root / "governance/meta_linguistic_registry.v1.json"
    if reg_path.is_file():
        from src.governance_organs.linguistic_governance_engine import LinguisticGovernanceEngine

        reg = load_json(reg_path)
        reg["last_work_order_sync_at"] = now
        LinguisticGovernanceEngine(root).save_registry(reg)

    return written


def set_work_order_status(
    gene: str,
    status: str,
    *,
    root: Path | None = None,
    operator_notes: str | None = None,
) -> dict[str, Any]:
    if status not in VALID_STATUSES:
        raise ValueError(f"invalid status {status!r}; expected one of {sorted(VALID_STATUSES)}")
    root = root or repo_root()
    wo = load_work_order(gene, root)
    if not wo:
        sync_work_orders_from_queue(root)
        wo = load_work_order(gene, root)
    if not wo:
        raise FileNotFoundError(f"no work order for gene {gene!r}; sync queue first")
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    wo["status"] = status
    wo["updated_at"] = now
    if operator_notes is not None:
        wo["operator_notes"] = operator_notes
    path = work_order_path(gene, root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(wo, indent=2) + "\n", encoding="utf-8")
    return wo


def work_order_summary(root: Path | None = None) -> dict[str, Any]:
    orders = load_all_work_orders(root)
    counts = {s: 0 for s in VALID_STATUSES}
    for wo in orders.values():
        st = wo.get("status", "pending")
        if st in counts:
            counts[st] += 1
    return {
        "total": len(orders),
        "pending": counts["pending"],
        "acknowledged": counts["acknowledged"],
        "completed": counts["completed"],
        "deferred": counts["deferred"],
    }


def pending_urgent_stale(
    root: Path | None = None,
    *,
    top_n: int = 5,
    max_pending_days: int = 14,
) -> list[dict[str, Any]]:
    """Return pending work orders older than max_pending_days among top-N queue genes."""
    root = root or repo_root()
    queue = load_governance_queue(root)
    if not queue:
        return []
    genes = [
        item["gene"]
        for item in (queue.get("items") or [])[:top_n]
        if item.get("gene")
    ]
    stale: list[dict[str, Any]] = []
    now = datetime.now(timezone.utc)
    for gene in genes:
        wo = load_work_order(gene, root)
        if not wo or wo.get("status") != "pending":
            continue
        updated = wo.get("updated_at") or wo.get("queue_generated_at", "")
        try:
            ts = datetime.fromisoformat(updated.replace("Z", "+00:00"))
        except ValueError:
            continue
        age_days = (now - ts).total_seconds() / 86400
        if age_days > max_pending_days:
            stale.append({"gene": gene, "age_days": round(age_days, 1), "urgency_score": wo.get("urgency_score")})
    return stale
