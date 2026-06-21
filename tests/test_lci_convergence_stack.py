"""LCI stack — convergence algebra, continuity lattice, creation operator, universal semantics."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.continuity.continuity_lattice import (
    convergence_respects_lattice,
    lci_holds,
    trace_join,
    trace_leq,
)
from src.continuity.convergence_algebra import (
    converge_many,
    converge_pair,
    d_conv,
    verify_magma_laws,
)
from src.continuity.creation_operator import CreationOperator, LCIViolation, SubstrateState
from src.continuity.lci_stack import apply_lci_stack, run_convergence_algebra_proof, run_creation_operator_proof
from src.continuity.lineage import Lineage
from src.continuity.universal_semantics import DEFAULT_META_LATTICE, DEFAULT_UNIVERSAL_FIELD, verify_meaning


def _lineage(
    lineage_id: str,
    events: list[str],
    *,
    meaning: str = "uui.continuity-preserving-creation",
    g: float = 1.0,
) -> Lineage:
    return Lineage(
        lineage_id=lineage_id,
        event_ids=frozenset(events),
        meaning_class=meaning,
        generativity=g,
    )


def test_continuity_lattice_join_and_lci() -> None:
    before = _lineage("L0", ["e1"], g=1.0)
    after = _lineage("L1", ["e1", "e2"], g=2.0)
    assert trace_leq(frozenset({"e1"}), frozenset({"e1", "e2"}))
    assert trace_join(frozenset({"e1"}), frozenset({"e2"})) == frozenset({"e1", "e2"})
    assert lci_holds(before, after)


def test_convergence_algebra_magma_and_metric() -> None:
    left = _lineage("La", ["e1", "e2"], g=2.0)
    right = _lineage("Lb", ["e1", "e3"], g=3.0)
    merged, proof = converge_pair(left, right)
    assert convergence_respects_lattice(left, right, merged)
    assert merged.generativity == 3.0
    assert proof.distance_left <= 0.35
    laws = verify_magma_laws(left, right, left)
    assert laws["idempotent"]
    assert laws["commutative"]
    assert laws["associative"]


def test_creation_operator_enforces_lci() -> None:
    state = SubstrateState(state_id="s0", lineage=_lineage("L0", ["e1"], g=1.0))
    operator = CreationOperator()
    nxt = operator.create(state, add_events=frozenset({"e2"}), generativity_delta=1.0)
    assert lci_holds(state.lineage, nxt.lineage)
    with pytest.raises(LCIViolation):
        operator.create(nxt, add_events=frozenset(), generativity_delta=-0.5)


def test_universal_and_meta_universal_layers() -> None:
    lineage = _lineage("Lu", ["e1"], meaning=DEFAULT_UNIVERSAL_FIELD.meaning_class)
    assert verify_meaning(lineage.meaning_class, DEFAULT_UNIVERSAL_FIELD.meaning_class)
    lattice = DEFAULT_META_LATTICE
    assert lattice.refines("uui.lawful-creation", "uui.no-annihilation-of-continuity")
    coherence = lattice.coherence(
        {"uui.continuity-preserving-creation", "uui.no-annihilation-of-continuity"}
    )
    assert coherence["coherent"]


def test_lci_stack_proofs_pass() -> None:
    assert run_convergence_algebra_proof()["passed"] is True
    assert run_creation_operator_proof()["passed"] is True


def test_apply_lci_stack_idempotent(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    online = tmp_path / "online"
    online.mkdir()
    monkeypatch.setenv("MEANING_LEDGER_PATH", str(online / "meaning-ledger.jsonl"))

    first = apply_lci_stack()
    second = apply_lci_stack()
    assert first["stack_ready"] is True
    assert first["lci_entries_added"] == 3
    assert second["lci_entries_added"] == 0
    assert second["convergence_algebra"]["passed"] is True


def test_converge_many_fixture_lineages() -> None:
    proof = run_convergence_algebra_proof()
    assert proof["merged_event_count"] >= 4
    assert proof["generativity"] >= 4.0
    assert d_conv(
        _lineage("x", ["a"]),
        _lineage("y", ["b"], meaning="other"),
    ) == 1.0
