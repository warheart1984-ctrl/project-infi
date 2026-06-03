#!/usr/bin/env python3
"""Tests for governed direct pipeline attestation enforcement (Wave 17)."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def test_pipeline_blocks_on_stale_attestation(tmp_path: Path, monkeypatch):
    gov = tmp_path / "governance"
    gov.mkdir(parents=True)
    (gov / "meta_linguistic_registry.v1.json").write_text(
        json.dumps(
            {
                "meta_linguistic_registry_version": "meta_linguistic_registry.v1",
                "policy_mode": "enforce",
            }
        ),
        encoding="utf-8",
    )
    (gov / "linguistic_governance_cadence_policy.v1.json").write_text(
        json.dumps(
            {
                "version": "linguistic_governance_cadence_policy.v1",
                "enforce_block_on_stale_attestation": True,
                "enforce_block_on_unaligned_attested_loop": False,
                "enforce_block_on_unaligned_governed_lifecycle": False,
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.chdir(tmp_path)
    with patch("src.governance_organs._paths.repo_root", return_value=tmp_path):
        with patch(
            "src.operator_cognition_coherence_fabric._root", return_value=tmp_path
        ):
            with patch(
                "src.operator_cognition_coherence_fabric.build_coherence_fabric_status",
                return_value={
                    "fabric_genes_aligned": True,
                    "coherence_pipeline_allowed": True,
                    "envelope_governance_modes": [],
                    "linguistic_attested_closed_loop_aligned": True,
                    "linguistic_governed_lifecycle_aligned": True,
                },
            ):
                with patch(
                    "src.governance_organs.linguistic_governance_attestation_engine.attestation_stale",
                    return_value=True,
                ):
                    with patch(
                        "src.governance_organs.linguistic_governance_attestation_engine.load_attestation",
                        return_value=None,
                    ):
                        from src.governed_direct_pipeline import build_governed_turn_pipeline

                        trace = build_governed_turn_pipeline(
                            contract="direct_answer",
                            response_mode="fast",
                        )
    assert trace.get("coherence_protocol", {}).get("response") == "BLOCK"
    assert "attestation" in (
        trace.get("coherence_protocol", {}).get("reason") or ""
    ).lower()
