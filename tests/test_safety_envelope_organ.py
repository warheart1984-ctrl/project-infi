"""Tests for safety_envelope_organ."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from src.safety_envelope import (
    HALT_ENV,
    SIGNAL_FILENAME,
    SIGNAL_VERSION,
    build_envelope_status,
    load_halt_signal,
    load_swarm_law_excerpt,
)


def test_build_envelope_status():
    status = build_envelope_status(root=Path(__file__).resolve().parents[1])
    assert status["safety_envelope_organ_version"] == "safety_envelope_organ.v1"
    assert status["envelope_id"] == "default"
    assert "thresholds" in status
    assert status["read_only"] is True


def test_doctrine_text_never_sets_halt_required():
    root = Path(__file__).resolve().parents[1]
    excerpt = load_swarm_law_excerpt(root=root).lower()
    assert "halt" in excerpt
    assert "crossed" in excerpt
    status = build_envelope_status(root=root)
    assert status["thresholds"]["halt_required"] is False


def test_runtime_signal_file_sets_halt_required(tmp_path, monkeypatch):
    monkeypatch.delenv(HALT_ENV, raising=False)
    signal_dir = tmp_path / ".runtime" / "governance"
    signal_dir.mkdir(parents=True)
    signal_path = signal_dir / SIGNAL_FILENAME
    signal_path.write_text(
        json.dumps(
            {
                "signal_version": SIGNAL_VERSION,
                "halt_required": True,
                "issuer": "operator",
                "reason": "pytest governed halt",
                "issued_at_utc": "2026-06-07T00:00:00Z",
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    loaded = load_halt_signal(root=tmp_path)
    assert loaded["halt_required"] is True
    assert loaded["source"] == "runtime_signal"
    status = build_envelope_status(root=tmp_path)
    assert status["thresholds"]["halt_required"] is True


def test_env_override_sets_halt_required(monkeypatch, tmp_path):
    monkeypatch.setenv(HALT_ENV, "1")
    loaded = load_halt_signal(root=tmp_path)
    assert loaded["halt_required"] is True
    assert loaded["source"] == "env"


def test_env_override_clears_halt(monkeypatch, tmp_path):
    signal_dir = tmp_path / ".runtime" / "governance"
    signal_dir.mkdir(parents=True)
    (signal_dir / SIGNAL_FILENAME).write_text(
        json.dumps({"signal_version": SIGNAL_VERSION, "halt_required": True}),
        encoding="utf-8",
    )
    monkeypatch.setenv(HALT_ENV, "0")
    loaded = load_halt_signal(root=tmp_path)
    assert loaded["halt_required"] is False
    assert loaded["source"] == "env"
