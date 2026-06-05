"""Governance Tier 5 — adaptive engine and gate."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]


@pytest.fixture(autouse=True)
def _repo(monkeypatch):
    monkeypatch.setenv("AAIS_REPO_ROOT", str(REPO))


def test_tier5_health_report_written():
    from src.governance_organs.adaptive_engine import Tier5Governance

    report = Tier5Governance.health_check(REPO)
    assert report["genome_count"] >= 8
    path = REPO / ".runtime/governance/tier5_health.json"
    assert path.is_file()
    data = json.loads(path.read_text(encoding="utf-8"))
    assert "stage_histogram" in data


def test_recipe_module_has_tier5_fields():
    from src.governance_organs import GenomeEngine

    reg = GenomeEngine.reload(REPO)
    gov = reg.genomes["recipe_module_organ"]["governance"]
    assert gov.get("operator_lanes")
    assert gov.get("contextual_gates")
    assert isinstance(gov["invariants"][0], dict)


def test_contextual_gate_no_block_by_default():
    from src.governance_organs.adaptive_engine import AdaptiveEngine

    result = AdaptiveEngine(REPO).evaluate_context("live_runtime", "mystic")
    assert not result.blocked


def test_tier5_gate_main():
    import subprocess
    import sys

    proc = subprocess.run(
        [sys.executable, str(REPO / "tools/governance/check_adaptive_governance.py")],
        cwd=REPO,
        check=False,
    )
    assert proc.returncode == 0
