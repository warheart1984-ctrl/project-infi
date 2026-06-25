"""Semantic memory store tests."""

from __future__ import annotations

import json
from pathlib import Path

from operator_kernel.memory.semantic_store import SemanticStore


def test_semantic_store_write_and_search(tmp_path: Path) -> None:
    store_path = tmp_path / "semantic.jsonl"
    store = SemanticStore(store_path)
    store.write("proj-a", "Refactor authentication middleware", task_id="t1", item_type="task_message")
    store.write("proj-a", "Unrelated database migration notes", task_id="t2", item_type="note")

    hits = store.search("proj-a", "authentication refactor", top_k=3)
    assert hits
    assert "authentication" in hits[0]["content"].lower()

    summary = store.summarize_for_prompt("proj-a", "auth work")
    assert "Relevant past work" in summary

    lines = store_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 2
    row = json.loads(lines[0])
    assert isinstance(row.get("embedding"), list)
