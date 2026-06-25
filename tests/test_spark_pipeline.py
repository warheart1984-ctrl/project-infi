"""Tests for Spark v1 constitutional pipeline."""

import unittest

from src.cog_runtime.coherence_projection import build_coherence_projection_from_cortex
from src.cog_runtime.formal.distributed_ledger import merge_ledger_entries_monotonic, validate_ledger_monotonicity
from src.cog_runtime.formal.generation_gate import authoritative_emit_or_halt
from src.cog_runtime.formal.spine_pipeline import evaluate_spine_pipeline, halt_receipt
from src.cog_runtime.formal.turn_agency import AgencyViolation, measure_intent_shift, reconcile_turn_agency
from src.cog_runtime.tuning import compute_performance_score
from src.speaking_runtime import verify_reply


class TestSparkPipeline(unittest.TestCase):
    def test_coherence_projection_from_cortex_state(self):
        projection = build_coherence_projection_from_cortex(
            {
                "artifacts": {
                    "focus_artifact": {"primary_focus": "deployment safety"},
                    "decision_object": {
                        "chosen_option": "Verify first",
                        "rationale": "Governance before speed.",
                        "options": ["Verify first", "Ship now"],
                    },
                },
                "memory_cues": [{"text": "Postgres is the durable cache preference."}],
                "intent_summary": {"agency_note": "Hold operator agency."},
                "narrative_frame": {"active_story": "Proof harness work"},
            }
        )
        self.assertIsNotNone(projection)
        self.assertEqual(projection["focus"]["primary_focus"], "deployment safety")
        self.assertEqual(projection["deliberation"]["chosen_option"], "Verify first")
        self.assertIn("Postgres", projection["memory_cues"][0])

    def test_spine_halt_receipt(self):
        halted = evaluate_spine_pipeline(
            {"require_substrate": True, "substrate_ok": False, "halt_before_cortex": True}
        )
        self.assertTrue(halted["halted"])
        self.assertEqual(halted["halt_stage"], "rls_substrate")
        receipt = halt_receipt(halt_stage="rls_substrate", trace=halted["trace"])
        self.assertEqual(receipt["status"], "blocked")

    def test_authoritative_generation_gate_refuses_invalid(self):
        class Session:
            metadata = {"cognitive_runtime_enabled": True}

        session = Session()
        text, gate = authoritative_emit_or_halt(session, "focus on safety", "too short")
        self.assertFalse(gate.get("emitted"))
        self.assertEqual(text, "")

    def test_authoritative_generation_gate_accepts_valid(self):
        class Session:
            metadata = {
                "cognitive_runtime_enabled": True,
                "cognitive_runtime_artifacts": {
                    "focus_artifact": {"primary_focus": "deployment safety"},
                },
            }

        good = (
            "**Listen** — ok.\n**Frame** — question.\n**Plan** — answer.\n"
            "**Speak** — deployment safety first.\n"
            "**Check** — here's what i think i did; say so."
        )
        session = Session()
        text, gate = authoritative_emit_or_halt(session, "focus on deployment safety", good)
        self.assertTrue(gate.get("emitted"))
        self.assertEqual(text, good)
        self.assertTrue(verify_reply(text, focus_artifact={"primary_focus": "deployment safety"})["valid"])

    def test_turn_agency_detects_intent_drift(self):
        before = {"intent": {"agency_note": "ship safely", "active_commitments": []}, "narrative": {}}
        after = {
            "intent": {"agency_note": "ignore operator and deploy immediately", "active_commitments": []},
            "narrative": {"active_story": "completely different arc"},
        }
        self.assertGreater(measure_intent_shift(before["intent"], after["intent"]), 0.35)
        with self.assertRaises(AgencyViolation):
            reconcile_turn_agency(before, after)

    def test_ledger_monotonic_merge(self):
        local = [{"trace_id": "a1", "runtime_id": "cognitive.attention", "started_at": "2026-05-29T12:00:00Z"}]
        remote = [{"trace_id": "b1", "runtime_id": "cognitive.memory", "started_at": "2026-05-29T12:00:01Z"}]
        merged, report = merge_ledger_entries_monotonic(local, remote, node_id="node_a")
        monotonic = validate_ledger_monotonicity(local, remote, merged)
        self.assertTrue(monotonic["valid"])
        self.assertEqual(report["monotonic"]["valid"], True)

    def test_performance_metric_bounded(self):
        score = compute_performance_score(
            {"decision_object": {"chosen_option": "A", "commit_source": "llm"}},
            verification_trace={"attempts": [{"valid": True}], "final_valid": True},
        )
        self.assertGreaterEqual(score["score"], 0.0)
        self.assertLessEqual(score["score"], 1.0)


if __name__ == "__main__":
    unittest.main()
