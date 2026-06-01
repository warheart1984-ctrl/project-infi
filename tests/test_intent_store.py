"""Tests for Nova Intent durable store and cross-session agency."""

import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from src.cog_runtime.intent_core import CONSTITUTIONAL_PROTECTED_VALUES, validate_intent_artifact
from src.cog_runtime.intent_store import (
    flush_nova_intent_store,
    load_intent_store,
    rehydrate_nova_intent,
    save_intent_store,
)
from src.cog_runtime.nova import configure_nova_cognitive_turn
from src.cogos_runtime_bridge import rehydrate_nova_intent_boot, seed_session_nova_intent


def _sample_intent(**overrides) -> dict:
    payload = {
        "version": "0.1",
        "active_commitments": [
            {"commitment": "Hold cross-session agency", "status": "active", "source": "test"}
        ],
        "protected_values": list(CONSTITUTIONAL_PROTECTED_VALUES),
        "long_horizon_goals": ["Persistent continuity"],
        "current_tensions": [
            {"poles": ["present", "future"], "pull": "future", "reason": "Multi-turn arc."}
        ],
        "agency_note": "Still committed to Persistent continuity while pulled toward future (1 active commitment(s)).",
        "stages_completed": ["orient", "tensions", "commitments", "persist"],
    }
    payload.update(overrides)
    return payload


class TestIntentStore(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.store_root = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_save_and_load_round_trip(self):
        intent = _sample_intent()
        path = save_intent_store("operator", intent, store_root=self.store_root)
        self.assertTrue(str(path).endswith("operator.intent.json"))
        record = load_intent_store("operator", store_root=self.store_root)
        self.assertIsNotNone(record)
        loaded = record["intent"]
        self.assertTrue(validate_intent_artifact(loaded)["valid"])
        self.assertEqual(loaded["agency_note"], intent["agency_note"])

    def test_cross_session_rehydration(self):
        session1 = SimpleNamespace(metadata={"nova_face": {"scope": "operator"}, "session_id": "s1"})
        intent = _sample_intent()
        flush_nova_intent_store(session1, intent, store_root=self.store_root)

        session2 = SimpleNamespace(metadata={"nova_face": {"scope": "operator"}, "session_id": "s2"})
        rehydrated = rehydrate_nova_intent(session2, store_root=self.store_root)
        self.assertIsNotNone(rehydrated)
        self.assertEqual(
            rehydrated["active_commitments"][0]["commitment"],
            intent["active_commitments"][0]["commitment"],
        )
        self.assertIn("nova_intent_store", session2.metadata)

    def test_configure_companion_turn_persists_intent(self):
        session = SimpleNamespace(metadata={"nova_face": {"scope": "proof-operator"}, "session_id": "s1"})
        with tempfile.TemporaryDirectory() as tmp:
            store_root = Path(tmp)
            configure_nova_cognitive_turn(
                session,
                {
                    "nova_intent_store": str(store_root),
                    "nova_intent_persist": True,
                    "nova_narrative": False,
                },
                "Should I pick the fast path or the safe path?",
                companion_turn=True,
            )
            record = load_intent_store("proof-operator", store_root=store_root)
            self.assertIsNotNone(record)
            self.assertTrue(validate_intent_artifact(record["intent"])["valid"])

    def test_boot_rehydrate_bridge(self):
        intent = _sample_intent()
        save_intent_store("boot-test", intent, store_root=self.store_root)
        boot = rehydrate_nova_intent_boot("boot-test", store_root=self.store_root)
        self.assertTrue(boot["rehydrated"])
        self.assertEqual(
            boot["active_commitments"][0]["commitment"],
            intent["active_commitments"][0]["commitment"],
        )

    def test_seed_session_intent(self):
        intent = _sample_intent()
        save_intent_store("seed-op", intent, store_root=self.store_root)
        metadata = seed_session_nova_intent({}, "seed-op", store_root=self.store_root)
        self.assertIn("nova_intent", metadata)
        self.assertEqual(metadata["nova_intent"]["agency_note"], intent["agency_note"])


if __name__ == "__main__":
    unittest.main()
