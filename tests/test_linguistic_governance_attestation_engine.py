#!/usr/bin/env python3
"""Tests for linguistic_governance_attestation_engine (Wave 14)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.governance_organs.linguistic_governance_attestation_engine import (  # noqa: E402
    build_attestation,
    list_attestation_cycles,
    write_attestation,
)


def test_build_attestation_fields():
    att = build_attestation(ROOT)
    assert att["linguistic_governance_attestation_version"] == (
        "linguistic_governance_attestation.v1"
    )
    assert 0 <= att["closed_loop_score"] <= 100
    assert "registry_summary" in att
    assert "forecast_summary" in att
    assert "calibration_summary" in att
    assert "queue_summary" in att
    assert "work_order_summary" in att
    assert isinstance(att["recommendations"], list)


def test_write_attestation(tmp_path: Path):
    import shutil

    for name in (
        "meta_linguistic_registry.v1.json",
        "linguistic_governance_cadence_policy.v1.json",
    ):
        src = ROOT / "governance" / name
        if src.is_file():
            dst = tmp_path / "governance" / name
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(src, dst)

    path = write_attestation(tmp_path)
    assert path.is_file()
    att = build_attestation(tmp_path)
    assert att["generated_at"]
    cycles = list_attestation_cycles(tmp_path)
    assert len(cycles) >= 1


def test_attestation_history_prune(tmp_path: Path):
    import shutil

    dst = tmp_path / "governance"
    dst.mkdir(parents=True, exist_ok=True)
    for name in (
        "linguistic_governance_cadence_policy.v1.json",
        "meta_linguistic_registry.v1.json",
    ):
        src = ROOT / "governance" / name
        if src.is_file():
            shutil.copy(src, dst / name)
    src_policy = dst / "linguistic_governance_cadence_policy.v1.json"
    if src_policy.is_file():
        data = json.loads(src_policy.read_text(encoding="utf-8"))
        data["retain_attestation_history"] = 2
        src_policy.write_text(json.dumps(data), encoding="utf-8")
    for _ in range(4):
        write_attestation(tmp_path)
    cycles = list_attestation_cycles(tmp_path)
    assert len(cycles) <= 2
