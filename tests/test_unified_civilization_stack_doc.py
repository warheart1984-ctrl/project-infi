"""Tests for the Unified Civilization Stack v1.0 architecture artifact."""

from __future__ import annotations

import json
import re
from pathlib import Path


DOC = Path(__file__).resolve().parents[1] / "docs" / "architecture" / "unified-civilization-stack-v1.0.md"


def _json_blocks(text: str) -> list[dict]:
    blocks = re.findall(r"```json\n(.*?)\n```", text, flags=re.DOTALL)
    return [json.loads(block) for block in blocks]


def test_unified_civilization_stack_doc_exists_and_names_layers() -> None:
    text = DOC.read_text(encoding="utf-8")

    for phrase in (
        "Civilization Memory Layer (FOS)",
        "Cognitive Layer (DAR-Z)",
        "Governance Layer",
        "Community / Ecological / Economic Layers",
        "Legacy Layer",
    ):
        assert phrase in text


def test_fos_darz_interface_json_examples_are_valid() -> None:
    blocks = _json_blocks(DOC.read_text(encoding="utf-8"))

    assert len(blocks) == 2
    assert blocks[0]["continuity_thread_id"] == "thread-uuid"
    assert "memory_refs" in blocks[0]
    assert blocks[1]["darz_continuity_thread_id"] == "thread-uuid"
    assert "reasoning_trace" in blocks[1]


def test_charter_contains_required_constitutional_articles() -> None:
    text = DOC.read_text(encoding="utf-8")

    for article in (
        "Non-Execution",
        "Evidence Binding",
        "Continuity Anchoring",
        "Invariant Disclosure",
        "Lineage Production",
        "Coherence Priority",
        "No Silent Failure",
    ):
        assert article in text


def test_memory_requirements_and_legacy_protocol_are_present() -> None:
    text = DOC.read_text(encoding="utf-8")

    for field in ("`id`", "`type`", "`definition`", "`evidence_refs`", "`lineage`", "`version`", "`continuity_thread`"):
        assert field in text
    for artifact_type in ("LegacyConstitution", "LegacyProtocol", "LegacyDecision", "LegacyBlueprint"):
        assert artifact_type in text
