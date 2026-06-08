"""Tests for adaptive immune hardening."""

from __future__ import annotations

import tempfile
import unittest

from src.immune_hardening import ImmuneHardeningStore
from src.immune_protocol import ImmuneResponse, apply_immune_protocol
from src.governed_direct_pipeline import build_pipeline_packet
from src.immune_protocol import DIRECT_COGNITIVE_LANE


def _packet(*, summary: str) -> dict:
    return build_pipeline_packet(
        source="llm",
        target="gb",
        lane=DIRECT_COGNITIVE_LANE,
        priority="normal",
        intent="result",
        state={"user_mode": "think", "system_mode": "stable", "risk_level": "low"},
        payload={
            "meaning": "governed_message",
            "tone": "neutral",
            "constraints": ["bounded_reply"],
            "summary": summary,
            "metadata": {},
        },
        route=["llm", "gb"],
    )


class TestImmuneHardening(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory(prefix="immune-hardening-")
        self.store = ImmuneHardeningStore(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_repeat_threat_raises_response_floor(self):
        self.store.record_threat(threat_code="authority_bypass_attempt", severity="critical")
        self.store.record_threat(threat_code="authority_bypass_attempt", severity="critical")
        profile = self.store.profile_for_protocol()
        self.assertEqual(profile.min_floor_for_code("authority_bypass_attempt"), ImmuneResponse.REJECT)

    def test_increment_generation_tightens_summary_limit(self):
        self.store.increment_generation(reason="incident_closed")
        profile = self.store.profile_for_protocol()
        self.assertLess(profile.summary_char_limit(), 180)

    def test_hardening_profile_raises_packet_bloat_to_reject(self):
        for _ in range(2):
            self.store.record_threat(threat_code="packet_bloat", severity="low")
        profile = self.store.profile_for_protocol()
        verbose_summary = " ".join(["bounded"] * 80)
        evaluation = apply_immune_protocol(
            forward_packets=[_packet(summary=verbose_summary)],
            service_packets=[],
            return_packets=[],
            active_lane=DIRECT_COGNITIVE_LANE,
            direct_route=["llm", "gb", "jar"],
            hardening_profile=profile,
        )
        immune = evaluation["immune_protocol"]
        self.assertEqual(immune["response"], "REJECT")
        self.assertIn("packet_bloat", immune["threat_memory_hits"])


if __name__ == "__main__":
    unittest.main()
