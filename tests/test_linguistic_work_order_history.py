#!/usr/bin/env python3
"""Tests for Wave 17 work-order history retention."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.governance_organs.linguistic_governance_work_order_engine import (  # noqa: E402
    archive_work_order_snapshot,
    list_work_order_snapshots,
    render_governance_queue_markdown,
    set_work_order_status,
    sync_work_orders_from_queue,
)


def _seed_queue(root: Path) -> None:
    payload = {
        "linguistic_governance_queue_version": "linguistic_governance_queue.v1",
        "generated_at": "2026-06-01T12:00:00Z",
        "items": [
            {
                "gene": "hist_gene",
                "urgency_score": 50,
                "current_band": "medium",
                "predicted_band": "high",
                "sources": ["forecast"],
            }
        ],
    }
    gov = root / "governance"
    gov.mkdir(parents=True, exist_ok=True)
    (gov / "linguistic_governance_queue.v1.json").write_text(
        json.dumps(payload), encoding="utf-8"
    )
    (gov / "linguistic_governance_cadence_policy.v1.json").write_text(
        json.dumps({"retain_work_order_history": 2}),
        encoding="utf-8",
    )


def test_sync_creates_snapshot_and_prunes(tmp_path: Path):
    _seed_queue(tmp_path)
    sync_work_orders_from_queue(tmp_path)
    assert len(list_work_order_snapshots(tmp_path)) == 1
    set_work_order_status("hist_gene", "completed", root=tmp_path)
    sync_work_orders_from_queue(tmp_path)
    snaps = list_work_order_snapshots(tmp_path)
    assert len(snaps) <= 2


def test_render_markdown_includes_queue(tmp_path: Path):
    _seed_queue(tmp_path)
    sync_work_orders_from_queue(tmp_path)
    md = render_governance_queue_markdown(tmp_path)
    assert "hist_gene" in md
    assert "Work orders" in md


def test_archive_snapshot_manual(tmp_path: Path):
    _seed_queue(tmp_path)
    sync_work_orders_from_queue(tmp_path)
    path = archive_work_order_snapshot(tmp_path, reason="test")
    assert path is not None
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["reason"] == "test"
    assert "hist_gene" in data["work_orders"]
