"""Alt-6 governed eligibility checks."""

from __future__ import annotations

from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]


@pytest.fixture(autouse=True)
def _repo(monkeypatch):
    monkeypatch.setenv("AAIS_REPO_ROOT", str(REPO))


def test_fabric_minimum_eligibility_passes():
    from tools.governance.check_alt6_governed_eligibility import check_eligibility

    errors = check_eligibility(REPO)
    assert errors == []


def test_fabric_minimum_gene_list():
    from tools.governance.check_alt6_governed_eligibility import FABRIC_MINIMUM_GENES

    assert "adaptive_lane_organ" in FABRIC_MINIMUM_GENES
    assert len(FABRIC_MINIMUM_GENES) == 5
