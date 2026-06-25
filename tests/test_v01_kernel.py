"""Nova v0.1 — kernel loop, lineage fork, divergence/convergence acceptance tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.continuity.nova_kernel_loop import (
    GenesisEvent,
    NovaKernel,
    fork_lineage,
    handle_genesis_event,
    run_kernel_loop,
)
from src.continuity.operator_kernel_interface import OperatorFeedback, OperatorKernelInterface


@pytest.fixture
def kernel(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> NovaKernel:
    online = tmp_path / "online"
    online.mkdir()
    monkeypatch.setenv("AAIS_ONLINE_RUNTIME_DIR", str(online))
    monkeypatch.setenv("MEANING_LEDGER_PATH", str(online / "meaning-ledger.jsonl"))
    return NovaKernel(online_dir=online)


def test_genesis_kernel_loop_passes(kernel: NovaKernel) -> None:
    result = handle_genesis_event(GenesisEvent(), kernel)

    assert result.status == "ok"
    assert result.lineage == "L0-GENESIS"
    assert result.phi >= kernel.phi_min
    assert result.errors == []


def test_lineage_fork_preserves_invariants_and_phi(kernel: NovaKernel) -> None:
    handle_genesis_event(GenesisEvent(), kernel)
    new_lineage = fork_lineage(
        kernel,
        "L0-GENESIS",
        "L1-OPERATOR-WORKSPACE",
        "operator workspace",
    )

    assert new_lineage.parent_id == "L0-GENESIS"
    assert new_lineage.invariants_ref == kernel.get_lineage("L0-GENESIS").invariants_ref
    assert kernel.current_phi >= kernel.phi_min


def test_divergence_then_convergence_non_degradation(kernel: NovaKernel) -> None:
    handle_genesis_event(GenesisEvent(), kernel)
    fork_lineage(kernel, "L0-GENESIS", "L1-OPERATOR-WORKSPACE", "divergence test")
    phi_before = kernel.current_phi

    event = GenesisEvent()
    event.lineage = "L1-OPERATOR-WORKSPACE"
    event.event_id = "EVT-L1-DIVERGENCE-0001"
    result = run_kernel_loop(event, kernel)
    assert result.status == "ok"

    phi_after = kernel.current_phi
    assert phi_after >= kernel.phi_min
    assert phi_after >= phi_before - kernel.delta_max


def test_operator_kernel_interface_create_and_fork(kernel: NovaKernel) -> None:
    oki = OperatorKernelInterface(kernel=kernel)
    create = oki.create(GenesisEvent())
    fork = oki.fork("L0-GENESIS", "L1-OPERATOR-WORKSPACE", "oki fork")

    assert create.feedback == OperatorFeedback.ACCEPTED
    assert fork.feedback == OperatorFeedback.ACCEPTED
