"""Tests for unified memory governance membrane."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from src.cog_runtime.narrative import NOVA_CORE_IDENTITY
from src.cog_runtime.narrative_store import flush_nova_narrative_store
from src.memory_governance_membrane import (
    resolve_operator_identity_id,
    seed_session_memory_membrane,
)


def _sample_narrative() -> dict:
    return {
        "version": "1.0",
        "core_identity": NOVA_CORE_IDENTITY,
        "active_story": "Memory membrane test",
        "current_chapter": "unification",
        "becoming": "continuity",
        "working_on": "membrane",
        "open_threads": [],
        "promises": [],
        "last_growth": "membrane seeded",
        "continuity_answers": {"doing": "membrane", "done": "", "toward": "continuity"},
        "turn_delta": {},
        "stages_completed": ["persist"],
    }


class TestMemoryGovernanceMembrane(unittest.TestCase):
    def test_resolve_operator_identity(self):
        session = SimpleNamespace(metadata={"nova_face": {"scope": "operator"}})
        self.assertEqual(resolve_operator_identity_id(session), "operator")

    def test_seed_rehydrates_from_store(self):
        with tempfile.TemporaryDirectory() as tmp:
            store_root = Path(tmp) / "nova_narrative"
            session = SimpleNamespace(
                metadata={
                    "nova_face": {"scope": "operator"},
                    "nova_narrative_store_root": str(store_root),
                    "nova_intent_store_root": str(Path(tmp) / "nova_intent"),
                    "session_id": "s1",
                }
            )
            flush_nova_narrative_store(session, _sample_narrative(), store_root=store_root)
            session.metadata.pop("nova_narrative", None)
            membrane = seed_session_memory_membrane(session, companion_turn=True)
            self.assertTrue(membrane.get("narrative_rehydrated"))
            self.assertIn("nova_narrative", session.metadata)


if __name__ == "__main__":
    unittest.main()
