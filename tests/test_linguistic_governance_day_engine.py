#!/usr/bin/env python3
"""Tests for Wave 17 linguistic governance day engine."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.governance_organs.linguistic_governance_day_engine import (  # noqa: E402
    LinguisticGovernanceDayEngine,
)


def test_dry_run_day_no_persist(tmp_path: Path):
    engine = LinguisticGovernanceDayEngine(tmp_path)
    with patch.object(
        engine,
        "_gov",
    ) as mock_gov:
        mock_gov.return_value.run_all_gates.return_value = MagicMock(
            passed=True,
            policy_mode="observe",
            results=[],
            errors=[],
        )
        with patch(
            "src.governance_organs.linguistic_full_governance_cycle_engine.LinguisticFullGovernanceCycleEngine.run_cycle"
        ) as mock_cycle:
            mock_cycle.return_value = MagicMock(
                cycle_id="test",
                passed=True,
                phases={},
                errors=[],
                warnings=[],
            )
            report = engine.run_day(dry_run=True)
    assert report.passed is True
    assert not (tmp_path / "governance" / "linguistic_governance_days").exists()


def test_day_persists_artifact(tmp_path: Path):
    gov = tmp_path / "governance"
    gov.mkdir(parents=True)
    (gov / "meta_linguistic_registry.v1.json").write_text(
        json.dumps(
            {
                "meta_linguistic_registry_version": "meta_linguistic_registry.v1",
                "policy_mode": "observe",
                "gates": [],
            }
        ),
        encoding="utf-8",
    )
    engine = LinguisticGovernanceDayEngine(tmp_path)
    with patch(
        "src.governance_organs.linguistic_full_governance_cycle_engine.LinguisticFullGovernanceCycleEngine.run_cycle"
    ) as mock_cycle:
        mock_cycle.return_value = MagicMock(
            cycle_id="cycle1",
            passed=True,
            phases={"queue": "governance/linguistic_governance_queue.v1.json"},
            errors=[],
            warnings=[],
        )
        with patch.object(engine, "_gov") as mock_gov:
            mock_gov.return_value.run_all_gates.return_value = MagicMock(
                passed=True,
                policy_mode="observe",
                results=[],
                errors=[],
            )
            mock_gov.return_value.load_registry.return_value = json.loads(
                (gov / "meta_linguistic_registry.v1.json").read_text(encoding="utf-8")
            )
            mock_gov.return_value.save_registry = lambda reg: (
                gov / "meta_linguistic_registry.v1.json"
            ).write_text(json.dumps(reg), encoding="utf-8")
            with patch(
                "src.governance_organs.linguistic_governance_work_order_engine.sync_work_orders_from_queue",
                return_value=[],
            ):
                with patch(
                    "src.governance_organs.linguistic_governance_attestation_engine.write_attestation"
                ) as mock_att:
                    mock_att.return_value = gov / "linguistic_governance_attestation.v1.json"
                    report = engine.run_day(fast=True)
    assert report.passed
    day_dir = tmp_path / "governance" / "linguistic_governance_days"
    assert day_dir.is_dir()
    assert list(day_dir.glob("*.v1.json"))
