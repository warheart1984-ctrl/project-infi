"""Tests for imagine_generator_organ."""

from __future__ import annotations

from src.imagine_generator_organ import build_imagine_generator_status


def test_build_status():
    status = build_imagine_generator_status()
    assert status["imagine_generator_organ_version"] == "imagine_generator_organ.v1"
    assert status["read_only"] is True
    assert status["module_id"]
