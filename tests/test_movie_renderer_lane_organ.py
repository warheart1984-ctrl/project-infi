"""Tests for movie_renderer_lane_organ."""

from __future__ import annotations

from src.movie_renderer_lane_organ import build_movie_renderer_lane_status


def test_build_status():
    status = build_movie_renderer_lane_status()
    assert status["movie_renderer_lane_organ_version"] == "movie_renderer_lane_organ.v1"
    assert status["read_only"] is True
