"""Tests for Canonical Runtime Contract (CRC) v0.1."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.crk1.canonical_runtime_contract import (
    CRC_INVARIANT_IDS,
    CRCCycleContext,
    CRCRuntime,
    compute_proof_hooks,
    merkle_crc_ids,
    sha256_hex,
)
from src.crk1.schema_validator import CRK1SchemaValidator

FIXTURES = Path(__file__).resolve().parents[2] / "fixtures" / "crk1"


def test_crc_invariant_registry_has_seven_ids() -> None:
    assert len(CRC_INVARIANT_IDS) == 7
    assert CRC_INVARIANT_IDS[0] == "CRC-1"
    assert CRC_INVARIANT_IDS[-1] == "CRC-7"


def test_merkle_crc_ids_deterministic() -> None:
    a = merkle_crc_ids(list(CRC_INVARIANT_IDS))
    b = merkle_crc_ids(list(CRC_INVARIANT_IDS))
    assert a == b
    assert len(a) == 64


def test_proof_hooks_composite_receipt() -> None:
    hooks = compute_proof_hooks(
        reconstruction_source="abc123",
        invariants_checked=list(CRC_INVARIANT_IDS),
        artifact_produced={"type": "proof", "hash": "d" * 64},
        continuity_score=0.9,
        prior_continuity_score=0.85,
    )
    assert hooks.proof_recon == sha256_hex("abc123")
    assert len(hooks.composite_receipt()) == 64


def test_crc_runtime_run_cycle_appends_ledger() -> None:
    runtime = CRCRuntime()
    ctx = CRCCycleContext(
        project_state_hash=sha256_hex({"state": "genesis"}),
        contradictions=[],
        artifact_type="spec",
        artifact_body={"spec": "CRC v0.1"},
        memory_delta={"entry": "cycle-1"},
        continuity_score=0.8,
    )
    trace = runtime.run_cycle(ctx)
    assert trace.proof_receipt
    assert trace.proof_hooks is not None
    assert len(runtime.ledger) == 1
    CRK1SchemaValidator().validate("CanonicalTraceObject", trace.to_dict())


def test_crc7_rejects_continuity_regression() -> None:
    runtime = CRCRuntime()
    runtime.run_cycle(
        CRCCycleContext(
            project_state_hash=sha256_hex("s1"),
            contradictions=[],
            artifact_type="code",
            artifact_body={"module": "a"},
            memory_delta={},
            continuity_score=0.9,
        )
    )
    with pytest.raises(ValueError, match="CRC-7"):
        runtime.run_cycle(
            CRCCycleContext(
                project_state_hash=sha256_hex("s2"),
                contradictions=[],
                artifact_type="code",
                artifact_body={"module": "b"},
                memory_delta={},
                continuity_score=0.5,
            )
        )


def test_crc1_requires_reconstruction() -> None:
    runtime = CRCRuntime()
    with pytest.raises(ValueError, match="CRC-1"):
        runtime.run_cycle(
            CRCCycleContext(
                project_state_hash="",
                contradictions=[],
                artifact_type="trace",
                artifact_body={"t": 1},
                memory_delta={},
                continuity_score=0.7,
                reconstruction_completed=False,
            )
        )


def test_crc6_rejects_invariant_in_memory_delta() -> None:
    runtime = CRCRuntime()
    with pytest.raises(ValueError, match="CRC-6"):
        runtime.run_cycle(
            CRCCycleContext(
                project_state_hash=sha256_hex("s"),
                contradictions=[],
                artifact_type="proof",
                artifact_body={"p": 1},
                memory_delta={"invariant_override": True},
                continuity_score=0.7,
            )
        )


def test_genesis_r0_binding() -> None:
    runtime = CRCRuntime()
    anchor = runtime.bind_genesis_r0("r0" * 32)
    assert anchor["crc_version"] == "0.1"
    assert "r0_anchor" in anchor
    assert anchor["invariant_set"] == ",".join(CRC_INVARIANT_IDS)


def test_sample_canonical_trace_validates() -> None:
    runtime = CRCRuntime()
    trace = runtime.run_cycle(
        CRCCycleContext(
            project_state_hash="7a8b9c0d1e2f30415263748596a7b8c9d0e1f2031425364758697a8b9c0d1e2f",
            contradictions=[],
            artifact_type="proof",
            artifact_body={"package": "PGA-PKG-1"},
            memory_delta={"event": "post_genesis_authority_verified"},
            continuity_score=0.92,
        )
    )
    sample_path = FIXTURES / "sample_canonical_trace.json"
    on_disk = json.loads(sample_path.read_text(encoding="utf-8"))
    assert on_disk["invariants_checked"] == list(CRC_INVARIANT_IDS)
    CRK1SchemaValidator().validate("CanonicalTraceObject", trace.to_dict())
