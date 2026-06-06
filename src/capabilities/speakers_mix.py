"""Speakers downstream lane capability adapter."""

# Mythic: Speakers Mix
# Engineering: SpeakersMixEngine
from __future__ import annotations

from typing import Any

from src.capability_module import AAISCapabilityModule

SPEAKERS_LANE_COMPONENT_ID = "jarvis.capability.speakers_mix"


class SpeakersMixCapability(AAISCapabilityModule):
    module_name = "speakers_mix"
    supported_actions = frozenset({"mix", "status"})

    def __init__(self) -> None:
        super().__init__(provider_name="aais_speakers")
        self.handlers = {"mix": self._handle_mix, "status": self._handle_status}

    def _handle_status(self, payload: dict[str, Any]) -> dict[str, Any]:
        from src.speakers_lane_organ import build_speakers_lane_status

        return self._ok("status", {"lane": build_speakers_lane_status(), "standalone_lane": True})

    def _handle_mix(self, payload: dict[str, Any]) -> dict[str, Any]:
        cues = payload.get("cues") or {}
        return self._ok(
            "mix",
            {
                "mix_plan": {"cues": cues, "status": "governed_posture"},
                "standalone_lane": True,
            },
        )
