"""Linguistic governance work orders — Wave 14 operator execution posture."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.governance_organs._paths import repo_root
from src.governance_organs.linguistic_governance_queue_engine import (
    format_queue_markdown,
    load_governance_queue,
)
from tools.linguistic_genome_lib import load_json

WORK_ORDER_VERSION = "linguistic_governance_work_order.v1"
SNAPSHOT_VERSION = "linguistic_work_order_snapshot.v1"
VALID_STATUSES = frozenset({"pending", "acknowledged", "completed", "deferred"})


def work_orders_dir(root: Path | None = None) -> Path:
    root = root or repo_root()
    return root / "governance/linguistic_governance_work_orders"


def work_order_snapshots_dir(root: Path | None = None) -> Path:
    root = root or repo_root()
    return root / "governance/linguistic_work_order_snapshots"


def list_work_order_snapshots(root: Path | None = None) -> list[Path]:
    snap_dir = work_order_snapshots_dir(root)
    if not snap_dir.is_dir():
        return []
    return sorted(snap_dir.glob("*.v1.json"), key=lambda p: p.name, reverse=True)


def _cadence_policy(root: Path) -> dict[str, Any]:
    from src.governance_organs.linguistic_governance_attestation_engine import (
        load_cadence_policy,
    )

    return load_cadence_policy(root)


def _prune_work_order_history(root: Path, policy: dict[str, Any]) -> None:
    retain = int(policy.get("retain_work_order_history", 24))
    snap_dir = work_order_snapshots_dir(root)
    if not snap_dir.is_dir():
        return
    files = sorted(snap_dir.glob("*.v1.json"), key=lambda p: p.name, reverse=True)
    for old in files[retain:]:
        old.unlink(missing_ok=True)


def archive_work_order_snapshot(root: Path | None = None, *, reason: str = "sync") -> Path | None:
    """Write aggregate work-order snapshot after sync or bulk update."""
    root = root or repo_root()
    orders = load_all_work_orders(root)
    if not orders:
        return None
    now = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    snap_dir = work_order_snapshots_dir(root)
    snap_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "linguistic_work_order_snapshot_version": SNAPSHOT_VERSION,
        "snapshot_id": now,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "reason": reason,
        "summary": work_order_summary(root),
        "work_orders": orders,
    }
    path = snap_dir / f"{now}.v1.json"
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    _prune_work_order_history(root, _cadence_policy(root))
    return path


def archive_work_order_gene_snapshot(
    gene: str,
    work_order: dict[str, Any],
    *,
    root: Path | None = None,
) -> Path:
    """Per-gene snapshot when status changes."""
    root = root or repo_root()
    now = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    safe = gene.replace("/", "_").replace("\\", "_")
    snap_dir = work_order_snapshots_dir(root)
    snap_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "linguistic_work_order_snapshot_version": SNAPSHOT_VERSION,
        "snapshot_id": f"{now}_{safe}",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "reason": "status_change",
        "gene": gene,
        "work_order": work_order,
    }
    path = snap_dir / f"{now}_{safe}.v1.json"
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    _prune_work_order_history(root, _cadence_policy(root))
    return path


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

    archive_work_order_snapshot(root, reason="sync")
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
    prior_status = wo.get("status")
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    wo["status"] = status
    wo["updated_at"] = now
    if operator_notes is not None:
        wo["operator_notes"] = operator_notes
    path = work_order_path(gene, root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(wo, indent=2) + "\n", encoding="utf-8")
    if prior_status != status:
        archive_work_order_gene_snapshot(gene, wo, root=root)
    return wo


def complete_top_work_orders(root: Path | None = None, *, top_n: int = 5) -> list[str]:
    """Mark top-N queue genes as completed."""
    root = root or repo_root()
    sync_work_orders_from_queue(root)
    queue = load_governance_queue(root)
    if not queue:
        return []
    genes = [
        item["gene"]
        for item in (queue.get("items") or [])[:top_n]
        if item.get("gene")
    ]
    for gene in genes:
        set_work_order_status(gene, "completed", root=root)
    archive_work_order_snapshot(root, reason="complete_top")
    return genes


def export_work_orders_json(root: Path | None = None) -> dict[str, Any]:
    root = root or repo_root()
    return {
        "summary": work_order_summary(root),
        "work_orders": load_all_work_orders(root),
        "snapshot_count": len(list_work_order_snapshots(root)),
    }


def render_governance_queue_markdown(root: Path | None = None) -> str:
    """Queue table plus work-order status for operator review."""
    root = root or repo_root()
    queue = load_governance_queue(root)
    orders = load_all_work_orders(root)
    parts: list[str] = []
    if queue:
        parts.append(format_queue_markdown(queue))
    else:
        parts.append("# Linguistic governance queue\n\n(no queue artifact)\n")
    parts.extend(
        [
            "## Work orders",
            "",
            "| Gene | Status | Urgency | Updated |",
            "|------|--------|---------|---------|",
        ]
    )
    if queue:
        for item in queue.get("items") or []:
            gene = item.get("gene", "")
            wo = orders.get(gene) or {}
            parts.append(
                f"| `{gene}` | {wo.get('status', '—')} | "
                f"{wo.get('urgency_score', item.get('urgency_score', ''))} | "
                f"{wo.get('updated_at', '')} |"
            )
    else:
        for gene, wo in sorted(
            orders.items(), key=lambda x: -x[1].get("urgency_score", 0)
        ):
            parts.append(
                f"| `{gene}` | {wo.get('status')} | {wo.get('urgency_score')} | "
                f"{wo.get('updated_at', '')} |"
            )
    parts.append("")
    return "\n".join(parts)


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
