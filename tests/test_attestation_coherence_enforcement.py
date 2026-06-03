#!/usr/bin/env python3
"""Tests for Wave 16 attestation coherence enforcement."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.operator_cognition_coherence_fabric import (  # noqa: E402
    evaluate_attestation_coherence,
)


def test_observe_mode_allows(tmp_path: Path):
    reg = {
        "meta_linguistic_registry_version": "meta_linguistic_registry.v1",
        "policy_mode": "observe",
    }
    (tmp_path / "governance").mkdir(parents=True)
    (tmp_path / "governance/meta_linguistic_registry.v1.json").write_text(
        json.dumps(reg), encoding="utf-8"
    )
    result = evaluate_attestation_coherence(tmp_path)
    assert result.allowed is True


def test_enforce_blocks_low_score(tmp_path: Path):
    reg = {
        "meta_linguistic_registry_version": "meta_linguistic_registry.v1",
        "policy_mode": "enforce",
    }
    gov = tmp_path / "governance"
    gov.mkdir(parents=True)
    (gov / "meta_linguistic_registry.v1.json").write_text(json.dumps(reg), encoding="utf-8")
    (gov / "linguistic_governance_cadence_policy.v1.json").write_text(
        json.dumps(
            {
                "version": "linguistic_governance_cadence_policy.v1",
                "enforce_min_closed_loop_score": 90,
                "enforce_block_on_stale_attestation": False,
                "enforce_block_on_unaligned_attested_loop": False,
            }
        ),
        encoding="utf-8",
    )
    (gov / "linguistic_governance_attestation.v1.json").write_text(
        json.dumps(
            {
                "linguistic_governance_attestation_version": (
                    "linguistic_governance_attestation.v1"
                ),
                "generated_at": "2026-06-01T12:00:00Z",
                "closed_loop_score": 50,
            }
        ),
        encoding="utf-8",
    )
    result = evaluate_attestation_coherence(tmp_path)
    assert result.allowed is False
    assert "closed_loop_score" in (result.reason or "")
