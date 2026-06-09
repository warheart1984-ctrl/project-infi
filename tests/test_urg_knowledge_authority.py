"""Tests for urg_library integration in knowledge authority."""

from __future__ import annotations

from unittest.mock import MagicMock

from src.knowledge_authority import KnowledgeAuthority


def test_build_snapshot_includes_urg_library():
    memory_store = MagicMock()
    memory_store.list_memories.return_value = []
    authority = KnowledgeAuthority()
    snapshot = authority.build_snapshot(
        memory_store=memory_store,
        workspace_profile={},
        workspace_projects=[],
        document_store=None,
        live_research=None,
        urg_library={
            "query": "proven claim",
            "summary": "Loaded 1 URG library entries.",
            "entries": [
                {
                    "contribution_id": "cid-1",
                    "title": "Proven claim",
                    "summary": "proofs/x.json",
                    "epistemic_state": "proven",
                }
            ],
        },
        query="proven claim",
    )
    assert snapshot["urg_library"]["entries"]
    assert snapshot["summary"]["urg_library_count"] == 1
    urg_authorities = [
        row for row in snapshot["active_authorities"] if row.get("source_type") == "urg_library"
    ]
    assert urg_authorities
    assert urg_authorities[0]["status"] in {"active", "shadow", "derived", "canonical"}
