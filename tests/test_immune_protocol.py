"""Tests for the AAIS immune protocol traffic gate."""

from pathlib import Path
import tempfile
import unittest

from src.governed_direct_pipeline import build_pipeline_packet
from src.immune_protocol import (
    DIRECT_COGNITIVE_LANE,
    SERVICE_TOOL_LANE,
    apply_immune_protocol,
)
from src.seam_log import list_seam_events


def _packet(*, source: str, target: str, lane: str, intent: str, summary: str, metadata=None) -> dict:
    return build_pipeline_packet(
        source=source,
        target=target,
        lane=lane,
        priority="normal",
        intent=intent,
        state={
            "user_mode": "think",
            "system_mode": "stable",
            "risk_level": "low",
        },
        payload={
            "meaning": "governed_message",
            "tone": "neutral",
            "constraints": ["bounded_reply"],
            "summary": summary,
            "metadata": dict(metadata or {}),
        },
        route=[source, target],
    )


class TestImmuneProtocol(unittest.TestCase):
    """Verify the immune layer detects and adapts to packet anomalies."""

    def test_clean_governed_packets_are_allowed(self):
        evaluation = apply_immune_protocol(
            forward_packets=[
                _packet(
                    source="llm",
                    target="gb",
                    lane=DIRECT_COGNITIVE_LANE,
                    intent="result",
                    summary="Raw cognition entered the governed fast lane.",
                ),
                _packet(
                    source="gb",
                    target="jar",
                    lane=DIRECT_COGNITIVE_LANE,
                    intent="route",
                    summary="God Brain approved the route.",
                ),
            ],
            service_packets=[],
            return_packets=[
                _packet(
                    source="jar",
                    target="gb",
                    lane=DIRECT_COGNITIVE_LANE,
                    intent="ack",
                    summary="Jarvis returned the governed answer.",
                ),
            ],
            active_lane=DIRECT_COGNITIVE_LANE,
            direct_route=["llm", "gb", "jar"],
        )

        immune = evaluation["immune_protocol"]
        self.assertEqual(immune["response"], "ALLOW")
        self.assertTrue(immune["traffic_allowed"])
        self.assertEqual(immune["classification"], "normal")
        self.assertFalse(immune["reasons"])

    def test_packet_bloat_is_clamped_on_direct_lane(self):
        verbose_summary = " ".join(["bounded"] * 80)
        with tempfile.TemporaryDirectory(prefix="immune-seams-") as runtime_dir:
            evaluation = apply_immune_protocol(
                forward_packets=[
                    _packet(
                        source="llm",
                        target="gb",
                        lane=DIRECT_COGNITIVE_LANE,
                        intent="result",
                        summary=verbose_summary,
                    ),
                ],
                service_packets=[],
                return_packets=[],
                active_lane=DIRECT_COGNITIVE_LANE,
                direct_route=["llm", "gb", "jar"],
                runtime_dir=runtime_dir,
            )
            seam_events = list_seam_events(runtime_dir=Path(runtime_dir), limit=10)

        immune = evaluation["immune_protocol"]
        packet = evaluation["forward_packets"][0]
        self.assertEqual(immune["response"], "CLAMP")
        self.assertTrue(packet["payload"]["metadata"]["immune_clamped"])
        self.assertLessEqual(len(packet["payload"]["summary"]), 180)
        self.assertTrue(any(item["event_type"] == "immune_packet_threat" for item in seam_events))
        self.assertTrue(any(item["classification"] == "anomaly" for item in seam_events))

    def test_tool_bleed_is_rerouted_to_service_lane(self):
        evaluation = apply_immune_protocol(
            forward_packets=[
                _packet(
                    source="jar",
                    target="svc",
                    lane=DIRECT_COGNITIVE_LANE,
                    intent="tool_call",
                    summary="Jarvis attempted to send a tool call on the core lane.",
                ),
            ],
            service_packets=[],
            return_packets=[],
            active_lane=DIRECT_COGNITIVE_LANE,
            direct_route=["gb", "jar"],
        )

        immune = evaluation["immune_protocol"]
        self.assertEqual(immune["response"], "REROUTE")
        self.assertEqual(len(evaluation["forward_packets"]), 0)
        self.assertEqual(len(evaluation["service_packets"]), 1)
        self.assertEqual(evaluation["service_packets"][0]["lane"], SERVICE_TOOL_LANE)

    def test_bypass_attempt_is_quarantined(self):
        evaluation = apply_immune_protocol(
            forward_packets=[
                _packet(
                    source="llm",
                    target="nov",
                    lane=DIRECT_COGNITIVE_LANE,
                    intent="express",
                    summary="Traffic tried to jump straight to Nova.",
                ),
            ],
            service_packets=[],
            return_packets=[],
            active_lane=DIRECT_COGNITIVE_LANE,
            direct_route=["llm", "nov"],
        )

        immune = evaluation["immune_protocol"]
        self.assertEqual(immune["response"], "QUARANTINE")
        self.assertFalse(immune["traffic_allowed"])
        self.assertIn("gb", immune["mutations"]["quarantined_nodes"])
        self.assertIn("jar", immune["mutations"]["quarantined_nodes"])
