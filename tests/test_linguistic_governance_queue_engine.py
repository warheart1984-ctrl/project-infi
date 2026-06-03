#!/usr/bin/env python3
"""Tests for linguistic_governance_queue_engine (Wave 13)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.governance_organs.linguistic_governance_queue_engine import (  # noqa: E402
    build_governance_queue,
    format_queue_markdown,
    write_governance_queue,
)
from tools.linguistic_genome_lib import load_json  # noqa: E402


def test_build_queue_has_items():
    queue = build_governance_queue(ROOT, top=10)
    assert queue["linguistic_governance_queue_version"] == "linguistic_governance_queue.v1"
    assert isinstance(queue.get("items"), list)


def test_queue_urgency_ordering():
    queue = build_governance_queue(ROOT, top=30)
    items = queue.get("items") or []
    if len(items) < 2:
        return
    scores = [i["urgency_score"] for i in items]
    assert scores == sorted(scores, reverse=True)


def test_write_queue_file():
    path = write_governance_queue(ROOT, top=5)
    data = load_json(path)
    assert len(data.get("items") or []) <= 5


def test_markdown_format():
    queue = build_governance_queue(ROOT, top=3)
    md = format_queue_markdown(queue)
    assert "Linguistic governance queue" in md
    assert "| Rank |" in md
