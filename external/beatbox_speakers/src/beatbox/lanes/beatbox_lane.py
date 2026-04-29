"""
Beatbox — Lane Orchestrator
Routes score vs live mode. Single entry point for Story Forge integration.
"""
from __future__ import annotations

import logging
import os
from typing import Optional

from beatbox.adapters.base_adapter import BeatboxAdapter
from beatbox.adapters.deterministic_adapter import DeterministicAdapter
from beatbox.adapters.openai_adapter import OpenAIAdapter, OpenAIAdapterConfig
from beatbox.contracts import (
    BeatboxArtifact,
    BeatboxResult,
    LiveStateUpdate,
    ScoreRequest,
    SceneState,
)
from beatbox.live_lane import LiveLane
from beatbox.score_lane import ScoreLane

logger = logging.getLogger(__name__)


class BeatboxLane:
    """
    Top-level orchestrator.
    score()      → film pipeline (ScoreRequest → BeatboxArtifact)
    live_state() → game pipeline (LiveStateUpdate → SceneState + payload)
    Both return BeatboxResult — no raw exceptions cross this boundary.
    """

    def __init__(self, adapter: Optional[BeatboxAdapter] = None) -> None:
        self._adapter = adapter or DeterministicAdapter()
        self._score_lane = ScoreLane(self._adapter)
        self._live_lane = LiveLane(self._adapter)

    @classmethod
    def from_env(cls) -> BeatboxLane:
        """Build lane from environment variables."""
        provider = os.environ.get("BEATBOX_PROVIDER", "deterministic").lower()
        if provider == "openai":
            config = OpenAIAdapterConfig.from_env()
            if config.available:
                adapter: BeatboxAdapter = OpenAIAdapter(config)
                logger.info("Beatbox: using OpenAI adapter (model=%s)", config.model)
            else:
                logger.warning("Beatbox: BEATBOX_PROVIDER=openai but no key found, using deterministic")
                adapter = DeterministicAdapter()
        else:
            adapter = DeterministicAdapter()
            logger.info("Beatbox: using deterministic adapter")
        return cls(adapter=adapter)

    # ── Score mode ────────────────────────────────────────────────────────────

    def score(self, request: ScoreRequest) -> BeatboxResult:
        """Film pipeline entry point. Always returns BeatboxResult."""
        try:
            artifact = self._score_lane.score(request)
            return BeatboxResult.success(artifact, mode="score")
        except Exception as exc:  # noqa: BLE001
            logger.error("BeatboxLane.score failed: %s", exc)
            return BeatboxResult.failure(
                error_type="ScoreError",
                message="Score lane failed",
                details={"exception": str(exc)},
                mode="score",
            )

    # ── Live mode ─────────────────────────────────────────────────────────────

    def live_state(self, update: LiveStateUpdate) -> BeatboxResult:
        """Game pipeline entry point. Returns live state payload in BeatboxResult."""
        try:
            payload = self._live_lane.get_live_payload(update)
            # Wrap payload in a minimal artifact for consistent contract shape
            artifact = BeatboxArtifact(
                session_id=update.game_state.get("session_id", "live"),
                scene_id=update.game_state.get("scene_id", "live"),
                audio_path="",           # no file in live mode
                timeline_path="",
                mode="live",
                provider=self._adapter.provider_name,
                continuity_passed=True,
                cue_count=0,
                total_duration_seconds=0.0,
                cues=[],
            )
            # Attach live payload as extra data — callers access via result.data
            artifact.__dict__["live_payload"] = payload
            return BeatboxResult.success(artifact, mode="live")
        except Exception as exc:  # noqa: BLE001
            logger.error("BeatboxLane.live_state failed: %s", exc)
            return BeatboxResult.failure(
                error_type="LiveStateError",
                message="Live state resolution failed",
                details={"exception": str(exc)},
                mode="live",
            )
