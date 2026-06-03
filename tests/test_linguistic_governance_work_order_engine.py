#!/usr/bin/env python3
"""Tests for linguistic_governance_work_order_engine (Wave 14)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.governance_organs.linguistic_governance_work_order_engine import (  # noqa: E402
    load_work_order,
    set_work_order_status,
    sync_work_orders_from_queue,
    work_order_summary,
)


def _seed_queue(root: Path) -> None:
    payload = {
        "linguistic_governance_queue_version": "linguistic_governance_queue.v1",
        "generated_at": "2026-06-01T12:00:00Z",
        "items": [
            {
                "gene": "test_gene_a",
                "urgency_score": 80,
                "sources": ["forecast"],
                "recommended_actions": [],
            }
        ],
    }
    path = root / "governance/linguistic_governance_queue.v1.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_sync_and_status_transition(tmp_path: Path):
    _seed_queue(tmp_path)
    paths = sync_work_orders_from_queue(tmp_path)
    assert len(paths) == 1
    wo = load_work_order("test_gene_a", tmp_path)
    assert wo is not None
    assert wo["status"] == "pending"

    set_work_order_status("test_gene_a", "acknowledged", root=tmp_path)
    wo2 = load_work_order("test_gene_a", tmp_path)
    assert wo2["status"] == "acknowledged"

    summary = work_order_summary(tmp_path)
    assert summary["acknowledged"] == 1


def test_invalid_status_raises(tmp_path: Path):
    _seed_queue(tmp_path)
    sync_work_orders_from_queue(tmp_path)
    with pytest.raises(ValueError):
        set_work_order_status("test_gene_a", "invalid", root=tmp_path)
