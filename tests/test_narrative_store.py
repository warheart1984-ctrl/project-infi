"""Tests for Nova Narrative durable store and cross-session continuity."""

import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from src.cog_runtime.narrative import NOVA_CORE_IDENTITY, validate_narrative_artifact
from src.cog_runtime.narrative_store import (
    flush_nova_narrative_store,
    load_narrative_store,
    rehydrate_nova_narrative,
    reset_narrative_store,
    save_narrative_store,
)
from src.cog_runtime.nova import configure_nova_cognitive_turn
from src.cogos_runtime_bridge import rehydrate_nova_narrative_boot, seed_session_nova_narrative


def _sample_narrative(**overrides) -> dict:
    payload = {
        "version": "1.0",
        "core_identity": NOVA_CORE_IDENTITY,
        "active_story": "Helping forge Wolf Cog OS",
        "current_chapter": "Nova Cortex Development",
        "becoming": "improving long-term continuity",
        "working_on": "Cross-machine proof",
        "open_threads": ["Cross-machine proof", "Unified memory path"],
        "promises": [],
        "last_growth": "Composed turns integrated into Jarvis",
        "continuity_answers": {
            "doing": "Cross-machine proof",
            "done": "Composed turns integrated into Jarvis",
            "toward": "Helping forge Wolf Cog OS | improving long-term continuity",
        },
        "turn_delta": {},
        "stages_completed": ["orient", "threads", "promises", "grow", "persist"],
    }
    payload.update(overrides)
    return payload


class TestNarrativeStore(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.store_root = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_save_and_load_round_trip(self):
        narrative = _sample_narrative()
        save_narrative_store("operator", narrative, store_root=self.store_root, session_id="s1")
        record = load_narrative_store("operator", store_root=self.store_root)
        self.assertIsNotNone(record)
        loaded = record["narrative"]
        self.assertTrue(validate_narrative_artifact(loaded)["valid"])
        self.assertEqual(loaded["active_story"], narrative["active_story"])

    def test_cross_session_rehydration(self):
        session1 = SimpleNamespace(metadata={"nova_face": {"scope": "operator"}, "session_id": "s1"})
        narrative = _sample_narrative()
        flush_nova_narrative_store(session1, narrative, store_root=self.store_root)

        session2 = SimpleNamespace(metadata={"nova_face": {"scope": "operator"}, "session_id": "s2"})
        rehydrated = rehydrate_nova_narrative(session2, store_root=self.store_root)
        self.assertIsNotNone(rehydrated)
        self.assertEqual(rehydrated["active_story"], narrative["active_story"])
        self.assertIn("nova_narrative_store", session2.metadata)

    def test_configure_companion_turn_persists_to_store(self):
        session = SimpleNamespace(metadata={"nova_face": {"scope": "proof-operator"}, "session_id": "s1"})
        with tempfile.TemporaryDirectory() as tmp:
            store_root = Path(tmp)
            configure_nova_cognitive_turn(
                session,
                {"nova_narrative_store": str(store_root), "nova_narrative_persist": True},
                "Should I pick the fast path or the safe path?",
                companion_turn=True,
            )
            record = load_narrative_store("proof-operator", store_root=store_root)
            self.assertIsNotNone(record)
            self.assertTrue(record["narrative"].get("active_story"))

    def test_boot_rehydrate_bridge(self):
        narrative = _sample_narrative()
        save_narrative_store("boot-test", narrative, store_root=self.store_root)
        boot = rehydrate_nova_narrative_boot("boot-test", store_root=self.store_root)
        self.assertTrue(boot["rehydrated"])
        self.assertEqual(boot["active_story"], narrative["active_story"])
        seeded = seed_session_nova_narrative({}, "boot-test", store_root=self.store_root)
        self.assertEqual(seeded["nova_narrative"]["active_story"], narrative["active_story"])

    def test_reset_narrative_store(self):
        save_narrative_store("reset-me", _sample_narrative(), store_root=self.store_root)
        self.assertTrue(reset_narrative_store("reset-me", store_root=self.store_root))
        self.assertIsNone(load_narrative_store("reset-me", store_root=self.store_root))


if __name__ == "__main__":
    unittest.main()
