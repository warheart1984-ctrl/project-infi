"""Alt-7 governed eligibility checks."""

from __future__ import annotations

from pathlib import Path

from tools.governance.check_alt7_governed_eligibility import check_eligibility

ROOT = Path(__file__).resolve().parents[1]
GOVERNED_PROOF = ROOT / "docs/proof/platform/OPERATOR_COGNITION_COHERENCE_FABRIC_GOVERNED_PROOF.md"


def test_alt7_governed_eligibility_passes():
    errors = check_eligibility(ROOT)
    assert not errors, errors


def test_alt7_governed_eligibility_requires_governed_proof(tmp_path, monkeypatch):
    if not GOVERNED_PROOF.is_file():
        return
    missing = tmp_path / "missing_governed_proof.md"
    monkeypatch.setattr(
        "tools.governance.check_alt7_governed_eligibility.GOVERNED_PROOF",
        missing,
    )
    errors = check_eligibility(ROOT)
    assert any("governed proof" in err for err in errors)
