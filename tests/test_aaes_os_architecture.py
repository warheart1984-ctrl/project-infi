"""AAES-OS architecture layer tests — orchestrator, policy, invariants."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from src.aaes_os import (
    AAESRequest,
    CognitiveOrchestrator,
    InvariantEngine,
    PolicyEngine,
    TraceStore,
    UnifiedLinguisticSurface,
)
from src.aaes_os.invariant_engine import ARCHITECTURE_TO_RFC


class AaesOsArchitectureTests(unittest.TestCase):
    def test_orchestrator_happy_path(self):
        orchestrator = CognitiveOrchestrator()
        request = AAESRequest(
            prompt="  deploy staging service  ",
            actor_id="operator-1",
            metadata={"operation": "execute", "intent": "deploy"},
        )
        result = orchestrator.execute(request)

        self.assertFalse(result.blocked)
        self.assertEqual(result.status, "ok")
        self.assertEqual(len(result.steps), 5)
        self.assertTrue(result.explanation)
        self.assertEqual(len(orchestrator.bus.events_for_span(result.span_id)), 4)

        stored = orchestrator.trace_store.get(result.trace_id)
        self.assertIsNotNone(stored)
        self.assertEqual(stored["status"], "ok")
        self.assertEqual(len(stored["events"]), 4)

    def test_policy_block(self):
        orchestrator = CognitiveOrchestrator()
        request = AAESRequest(
            prompt="reset everything",
            actor_id="operator-1",
            metadata={"operation": "destructive_reset"},
        )
        result = orchestrator.execute(request)

        self.assertTrue(result.blocked)
        self.assertEqual(result.block_code, "AAES_POLICY_BLOCKED")
        self.assertEqual(result.status, "blocked")
        self.assertLess(len(result.steps), 5)
        self.assertEqual(len(orchestrator.bus.log), 0)

    def test_invariant_block(self):
        orchestrator = CognitiveOrchestrator()
        request = AAESRequest(
            prompt="valid prompt",
            actor_id="operator-1",
            metadata={"force_invariant_block": True},
        )
        result = orchestrator.execute(request)

        self.assertTrue(result.blocked)
        self.assertEqual(result.block_code, "AAES_INVARIANT_VIOLATION")
        self.assertEqual(len(orchestrator.bus.log), 0)

    def test_trace_store_jsonl_append(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = TraceStore(path=Path(tmp) / "traces.jsonl")
            orchestrator = CognitiveOrchestrator(trace_store=store)
            request = AAESRequest(prompt="index docs", actor_id="operator-2")
            result = orchestrator.execute(request)
            self.assertFalse(result.blocked)
            lines = (Path(tmp) / "traces.jsonl").read_text(encoding="utf-8").strip().splitlines()
            self.assertEqual(len(lines), 1)

    def test_invariant_mapping_covers_seven(self):
        self.assertEqual(len(ARCHITECTURE_TO_RFC), 7)
        self.assertIn("traceability", ARCHITECTURE_TO_RFC)
        self.assertIn("governance_first", ARCHITECTURE_TO_RFC)

    def test_uls_normalize_and_summarize(self):
        uls = UnifiedLinguisticSurface()
        normalized = uls.normalize_input("  hello   world  ")
        self.assertEqual(normalized, "hello world")
        score = uls.semantic_compare("hello world", "hello there world")
        self.assertGreater(score, 0.0)


if __name__ == "__main__":
    unittest.main()
