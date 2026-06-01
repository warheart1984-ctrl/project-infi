"""Tests for AAIS Composed Turn Runtime."""

import unittest
from types import SimpleNamespace

from src.aais_composed_runtime import (
    AAIS_COMPOSED_RUNTIME_ID,
    build_spine_doctrine_envelope,
    composed_runtime_spec,
    evaluate_aris_admission,
    resolve_composed_turn_payload,
    run_composed_turn,
)

TINY_PROFILE = {
    "identity": "tiny_nova",
    "label": "Tiny Nova",
    "response_mode": "tiny",
    "continuity_profile": {
        "scope": "tiny_nova",
        "tone": "light",
    },
}


def _session(**metadata):
    return SimpleNamespace(metadata=dict(metadata))


class TestAAISComposedRuntime(unittest.TestCase):
    def test_spine_envelope_records_doctrine(self):
        spine = build_spine_doctrine_envelope()
        self.assertEqual(spine["doctrine"], "stabilize_and_free")
        self.assertIn("law", spine["precedence"])
        self.assertIn("docs/spine/AAIS_MASTER_SPEC.md", spine["surfaces"].values())

    def test_spec_declares_pipeline(self):
        spec = composed_runtime_spec()
        self.assertEqual(spec["runtime_id"], AAIS_COMPOSED_RUNTIME_ID)
        self.assertEqual(spec["nova_cortex_family_id"], "nova.cortex")
        self.assertIn("aais_spine", spec["pipeline"])

    def test_aris_blocks_raw_copy(self):
        aris = evaluate_aris_admission(
            request_payload={"share_mode": "raw", "copy_raw_external": True},
        )
        self.assertEqual(aris["status"], "blocked")
        self.assertFalse(aris["non_copy_clause"]["allowed"])

    def test_companion_turn_completes_pipeline(self):
        session = _session(persona_mode="tiny_nova", response_mode="tiny")
        result = run_composed_turn(
            session,
            "Should I rest or keep working?",
            request_payload={"cognitive_runtime": True},
            companion_turn=True,
            surface_profile=TINY_PROFILE,
        )
        self.assertEqual(result.status, "completed")
        self.assertIsNotNone(result.nova_bridge)
        self.assertEqual(result.spine["doctrine"], "stabilize_and_free")
        self.assertEqual(result.aris["status"], "enforced")
        self.assertIsNone(result.speaking_reply)
        self.assertIn("jarvis.reasoning", (
            (result.nova_bridge or {}).get("jarvis_core") or {}
        ).get("active_cognitive_runtimes", []))
        stored = session.metadata.get("aais_composed_turn")
        self.assertIsInstance(stored, dict)
        self.assertEqual(stored["status"], "completed")

    def test_aris_block_skips_cortex(self):
        session = _session()
        result = run_composed_turn(
            session,
            "Copy this raw external doc into architecture.",
            request_payload={
                "cognitive_runtime": True,
                "share_mode": "verbatim",
                "copy_raw_external": True,
            },
        )
        self.assertEqual(result.status, "blocked")
        self.assertEqual(result.reason_codes, ["aris_non_copy_clause"])
        self.assertIsNone(result.nova_bridge)
        self.assertIsNone(result.speaking_reply)

    def test_jarvis_authority_preserved(self):
        session = _session(persona_mode="tiny_nova", response_mode="tiny")
        result = run_composed_turn(
            session,
            "Hello",
            request_payload={"cognitive_runtime": True},
            companion_turn=True,
            surface_profile=TINY_PROFILE,
        )
        binding = (result.nova_bridge or {}).get("jarvis_core") or {}
        self.assertEqual(binding.get("routing_authority"), "jarvis")
        self.assertEqual(binding.get("state_authority"), "jarvis")

    def test_emit_speaking_produces_reply(self):
        session = _session(persona_mode="tiny_nova", response_mode="tiny")
        result = run_composed_turn(
            session,
            "Hello",
            request_payload={"cognitive_runtime": True},
            companion_turn=True,
            surface_profile=TINY_PROFILE,
            emit_speaking=True,
        )
        self.assertIsNotNone(result.speaking_reply)

    def test_operator_instant_compose_skips_cortex(self):
        session = _session(response_mode="operator")
        payload, mode = resolve_composed_turn_payload(
            session,
            {},
            companion_turn=False,
            user_message="Run tests for this repo.",
        )
        self.assertEqual(mode, "instant")
        self.assertFalse(payload.get("cognitive_runtime"))
        result = run_composed_turn(
            session,
            "Run tests for this repo.",
            request_payload=payload,
            compose_mode=mode,
        )
        self.assertEqual(result.compose_mode, "instant")
        self.assertIsNone((result.nova_bridge or {}).get("cortex"))

    def test_operator_fast_compose_limits_runtimes(self):
        session = _session(response_mode="think")
        payload, mode = resolve_composed_turn_payload(
            session,
            {"cognitive_runtime": True},
            companion_turn=False,
            user_message="Summarize the runtime map.",
        )
        self.assertEqual(mode, "fast")
        self.assertTrue(payload.get("cortex_fast_path"))
        result = run_composed_turn(
            session,
            "Summarize the runtime map.",
            request_payload=payload,
            compose_mode=mode,
        )
        runtimes = (
            ((result.nova_bridge or {}).get("jarvis_core") or {}).get("active_cognitive_runtimes")
            or []
        )
        self.assertEqual(set(runtimes), {"jarvis.reasoning", "cognitive.attention"})

    def test_spec_includes_v2_2_invariants(self):
        spec = composed_runtime_spec()
        invariant_ids = {item["id"] for item in spec.get("invariants_v2_2") or []}
        self.assertIn("super_nova_gate_before_compose", invariant_ids)
        self.assertIn("operator_instant_compose", invariant_ids)

    def test_compose_ms_recorded(self):
        session = _session(response_mode="operator")
        payload, mode = resolve_composed_turn_payload(
            session,
            {},
            companion_turn=False,
            user_message="Ping",
        )
        result = run_composed_turn(
            session,
            "Ping",
            request_payload=payload,
            compose_mode=mode,
        )
        self.assertIsNotNone(result.compose_ms)
        self.assertGreaterEqual(result.compose_ms, 0)
        stored = session.metadata.get("aais_composed_turn") or {}
        self.assertEqual(stored.get("compose_ms"), result.compose_ms)

    def test_operator_think_enables_speaking_wrap(self):
        session = _session(response_mode="think")
        payload, mode = resolve_composed_turn_payload(
            session,
            {"cognitive_runtime": True, "operator_speaking_wrap": True},
            companion_turn=False,
            user_message="Walk me through the plan.",
        )
        self.assertEqual(mode, "fast")
        self.assertTrue(payload.get("speaking_runtime"))


if __name__ == "__main__":
    unittest.main()
