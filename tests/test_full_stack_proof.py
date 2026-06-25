"""Production-grade full stack proof tests."""

from __future__ import annotations

from src.cori.full_stack_proof import run_full_stack_proof


def test_full_stack_proof_in_process() -> None:
    report = run_full_stack_proof(mode="in_process")
    assert report.status == "pass", report.to_dict()
    layer_names = {layer.layer for layer in report.layers}
    assert "nova" in layer_names
    assert "ugr" in layer_names
    assert "aais" in layer_names
    assert "aaes" in layer_names
    assert "nexus" in layer_names
    assert "cori_invariants" in layer_names
    assert "cori_alpha_pel" in layer_names
    assert "cori_vault_cp001" in layer_names
    assert report.governed_trace is not None
    assert report.alpha_proof is not None
    assert report.vault_cp001 is not None
    assert all(inv["passed"] for inv in report.invariants)


def test_full_stack_proof_json_roundtrip() -> None:
    report = run_full_stack_proof(mode="in_process")
    parsed = report.to_dict()
    assert parsed["status"] in {"pass", "fail"}
    assert isinstance(parsed["layers"], list)
    assert parsed["summary"]
