"""Capability bridge routes for Alt-3 subsystem families."""

from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from src.capability_service_bridge import CapabilityServiceBridge
from src.phase_gate import reset_registry


class TestCapabilityBridgeAlt3(unittest.TestCase):
    def setUp(self) -> None:
        reset_registry()
        self.temp_root = Path(tempfile.mkdtemp(prefix="bridge_alt3_"))

    def tearDown(self) -> None:
        shutil.rmtree(self.temp_root, ignore_errors=True)

    def _build_bridge(self) -> CapabilityServiceBridge:
        return CapabilityServiceBridge(
            spatial_query=lambda mode, **kwargs: {"mode": mode, "visible": False},
            render_spatial=lambda args, result: "spatial",
            mystic_read=lambda text: {"state": "awakening", "next_action": "go"},
            render_mystic=lambda result: "mystic",
            v9_run=lambda **kwargs: {"status": "completed", "location": "Unknown"},
            render_v9=lambda result: "v9",
            v10_run=lambda **kwargs: {"status": "completed", "location": "Unknown"},
            render_v10=lambda result: "v10",
        )

    def test_snapshot_lists_alt3_capabilities(self) -> None:
        bridge = self._build_bridge()
        bridge.snapshot()
        registry = bridge.snapshot()["registry"]
        self.assertIn("recipe_module", registry)
        self.assertIn("imagine_generator", registry)
        self.assertIn("human_voice_extraction", registry)
        self.assertIn("forensic_triangulation", registry)
        self.assertIn("narrative_trust_pack", registry)
        ntp_actions = registry["narrative_trust_pack"]
        self.assertIn("pack", ntp_actions)
        self.assertIn("verify", ntp_actions)
        self.assertIn("signoff", ntp_actions)
        imagine_actions = registry["imagine_generator"]
        self.assertIn("emit", imagine_actions)
        self.assertIn("handoff", imagine_actions)
        self.assertIn("grok_render", imagine_actions)

    def test_recipe_create_mission_via_bridge(self) -> None:
        bridge = self._build_bridge()
        bridge.snapshot()
        result = bridge.execute_selection(
            "recipe_module",
            "create_mission",
            args={"recipe_id": "onboarding-v1", "signoff_ack": True},
            runtime_context="operator_runtime",
        )
        self.assertEqual(result["tool_result"]["status"], "completed")
        self.assertIn("Operator Onboarding", result["response"])

    def test_imagine_emit_and_handoff_via_bridge(self) -> None:
        bridge = self._build_bridge()
        bridge.snapshot()
        emit = bridge.execute_selection(
            "imagine_generator",
            "emit",
            args={"fixture": "scene-seed-demo"},
            runtime_context="operator_runtime",
        )
        self.assertEqual(emit["tool_result"]["status"], "completed")
        pattern_id = emit["tool_result"]["result"]["pattern_id"]
        handoff = bridge.execute_selection(
            "imagine_generator",
            "handoff",
            args={"pattern_id": pattern_id},
            runtime_context="operator_runtime",
        )
        self.assertEqual(handoff["tool_result"]["status"], "completed")

    def test_imagine_grok_render_blocked_without_keys(self) -> None:
        import os

        bridge = self._build_bridge()
        bridge.snapshot()
        for key in ("STORY_FORGE_XAI_API_KEY", "XAI_API_KEY"):
            os.environ.pop(key, None)
        emit = bridge.execute_selection(
            "imagine_generator",
            "emit",
            args={"fixture": "scene-seed-demo"},
            runtime_context="operator_runtime",
        )
        pattern_id = emit["tool_result"]["result"]["pattern_id"]
        grok = bridge.execute_selection(
            "imagine_generator",
            "grok_render",
            args={"pattern_id": pattern_id},
            runtime_context="operator_runtime",
        )
        self.assertIn(grok["tool_result"]["status"], {"failed", "blocked"})

    def test_human_voice_extract_signoff_handoff_via_bridge(self) -> None:
        bridge = self._build_bridge()
        bridge.snapshot()
        extract = bridge.execute_selection(
            "human_voice_extraction",
            "extract",
            args={"fixture": "notes-demo-redacted"},
            runtime_context="operator_runtime",
        )
        self.assertEqual(extract["tool_result"]["status"], "completed")
        extraction_id = extract["tool_result"]["result"]["extraction_id"]
        signoff = bridge.execute_selection(
            "human_voice_extraction",
            "signoff",
            args={"extraction_id": extraction_id, "signoff_by": "operator"},
            runtime_context="operator_runtime",
        )
        self.assertEqual(signoff["tool_result"]["status"], "completed")
        handoff = bridge.execute_selection(
            "human_voice_extraction",
            "handoff",
            args={"extraction_id": extraction_id},
            runtime_context="operator_runtime",
        )
        self.assertEqual(handoff["tool_result"]["status"], "completed")

    def test_forensic_triangulation_correlate_via_bridge(self) -> None:
        bridge = self._build_bridge()
        bridge.snapshot()
        tri_root = self.temp_root / "triangulation"
        result = bridge.execute_selection(
            "forensic_triangulation",
            "correlate",
            args={
                "case_id": "tri-demo-001",
                "fixture": "tri-demo-001",
                "triangulation_root": str(tri_root),
            },
            runtime_context="operator_runtime",
        )
        self.assertEqual(result["tool_result"]["status"], "completed")
        payload = result["tool_result"]["result"]
        self.assertEqual(payload.get("case_id"), "tri-demo-001")
        self.assertGreaterEqual(len(payload.get("correlation_edges") or []), 1)

    def test_narrative_trust_pack_pack_verify_signoff_via_bridge(self) -> None:
        bridge = self._build_bridge()
        bridge.snapshot()
        narrative_root = self.temp_root / "narrative"
        story = self.temp_root / "story.txt"
        beat = self.temp_root / "beat.wav"
        final = self.temp_root / "final.mp3"
        story.write_text("story artifact", encoding="utf-8")
        beat.write_bytes(b"beat")
        final.write_bytes(b"audio")
        pack = bridge.execute_selection(
            "narrative_trust_pack",
            "pack",
            args={
                "pack_id": "bridge-ntp-001",
                "author": "operator",
                "narrative_root": str(narrative_root),
                "capability_output": {
                    "metadata_path": str(story),
                    "music_stem_path": str(beat),
                    "final_audio_path": str(final),
                    "session_id": "bridge-session",
                },
            },
            runtime_context="operator_runtime",
        )
        self.assertEqual(pack["tool_result"]["status"], "completed")
        verify = bridge.execute_selection(
            "narrative_trust_pack",
            "verify",
            args={"pack_id": "bridge-ntp-001", "narrative_root": str(narrative_root)},
            runtime_context="operator_runtime",
        )
        self.assertEqual(verify["tool_result"]["status"], "completed")
        signoff = bridge.execute_selection(
            "narrative_trust_pack",
            "signoff",
            args={
                "pack_id": "bridge-ntp-001",
                "signoff_by": "operator",
                "narrative_root": str(narrative_root),
            },
            runtime_context="operator_runtime",
        )
        self.assertEqual(signoff["tool_result"]["status"], "completed")
        self.assertEqual(signoff["tool_result"]["result"].get("claim_label"), "proven")


if __name__ == "__main__":
    unittest.main()
