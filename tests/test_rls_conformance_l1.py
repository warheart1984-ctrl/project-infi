"""L1 Runtime Law Spine conformance tests."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from runtime_law_spine.runtime_law_spine.gate import RuntimeLawSpineGate
from runtime_law_spine.runtime_law_spine.startup import ensure_rls_sealed
from src.cog_runtime.formal.spine_pipeline import evaluate_spine_pipeline
from src.ucr.trust_root import reset_trust_root_for_tests


@pytest.fixture(autouse=True)
def _reset_rls_state(monkeypatch: pytest.MonkeyPatch) -> None:
    reset_trust_root_for_tests()
    RuntimeLawSpineGate._instance = None
    for key in (
        "UCR_CORRIDOR_REGISTRY",
        "UCR_LAW_SPINE",
        "UCR_KERNEL_IMAGE",
        "RLS_STRICT",
        "RLS_CONFORMANCE_LEVEL",
    ):
        monkeypatch.delenv(key, raising=False)


def test_sealed_dev_fixture_substrate_ok() -> None:
    gate = ensure_rls_sealed()
    assert gate.sealed is True
    assert gate.substrate_ok is True
    assert gate.trust_root_receipt is not None


def test_strict_mode_missing_registry_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RLS_STRICT", "1")
    monkeypatch.setenv("UCR_CORRIDOR_REGISTRY", str(Path("/nonexistent/corridor_registry")))
    monkeypatch.setenv("UCR_LAW_SPINE", "0")
    monkeypatch.setenv("UCR_KERNEL_IMAGE", "stub-kernel")

    with pytest.raises(RuntimeError, match="RLS boot failed"):
        ensure_rls_sealed()


def test_rls_substrate_fails_when_required_without_substrate() -> None:
    result = evaluate_spine_pipeline({"require_substrate": True})
    assert result["halted"] is True
    assert result["halt_stage"] == "rls_substrate"


def test_rls_substrate_passes_when_required_and_explicit() -> None:
    result = evaluate_spine_pipeline({"require_substrate": True, "substrate_ok": True})
    assert result["halted"] is False
