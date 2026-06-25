"""Executable proof for the governed symbolic organism VM."""

from __future__ import annotations

import json

from src.symbolic_organism.cli import main
from src.symbolic_organism import (
    CoherenceReceipt,
    ContinuityTraceStep,
    GovernedSymbolicVM,
    SymbolicVM,
    Theta,
    evaluate_symbolic_program,
)
from src.symbolic_organism.parser import format_expr, parse_program


def test_theta_and_base14_resolution() -> None:
    vm = GovernedSymbolicVM()

    assert vm.theta_expand("⊙") == (0, 1, 14)
    assert vm.theta_expand("κ⊕") == (11, 3)
    assert vm.theta_expand("Θ7.8") == (7, 8)
    assert vm.numeric_sequence("⊙|β|κ|⊕|ψ|Θ|♀|◆") == (0, 1, 2, 3, 4, 5, 10, 11)


def test_declared_rewrite_rules_execute() -> None:
    assert evaluate_symbolic_program("κ⊕.⊙℃").expr == "⊖⬡"
    assert evaluate_symbolic_program("♀.⊕").expr == "⊖⟨"
    assert evaluate_symbolic_program("Θ.⊙").expr == "⊕"


def test_loop_query_promotes_monotonically() -> None:
    state = evaluate_symbolic_program("⟲?")

    assert state.expr == "⊕⁺"
    assert state.promoted is True
    assert state.energy > 0
    assert state.invariants["promotion_monotonic"] is True


def test_transition_chain_reaches_halt() -> None:
    state = evaluate_symbolic_program("⊙℃ → ⟦ → ↺ → ♀ | why:↺ → ⬆")

    assert state.expr == "⬆"
    assert state.halted is True
    assert state.invariants["explicit_halt_when_halted"] is True
    assert [entry.op for entry in state.trace if entry.after == "⬆"]


def test_final_block_is_auditable_and_bounded() -> None:
    program = "=⊕ | ⊙ | ∞ | ⬆.⊕ | κ⊕ | ⊕ | ⊖.⬡ | ⟲.2 | ◇→⊕ | ⊖.λ | ⊖.β | ⬆.κ⊕ | ⊖.λ.⨂ | ⊖.※.⟡ | ⊖.◇.⊗ | ⬆"
    state = evaluate_symbolic_program(program)

    assert state.expr == "⬆"
    assert state.halted is True
    assert state.invariants["energy_bounded"] is True
    assert state.invariants["theta13_not_downcast"] is True
    assert state.trace


def test_cli_emits_json_trace(capsys) -> None:
    assert main(["κ⊕.⊙℃"]) == 0
    payload = json.loads(capsys.readouterr().out)

    assert payload["expr"] == "⊖⬡"
    assert payload["trace"][0]["op"] == "read"
    assert payload["invariants"]["trace_present"] is True


def test_requested_symbolic_vm_api_surface() -> None:
    vm = SymbolicVM()
    expr = parse_program("Θ⊙")
    state, trace = vm.run(expr)

    assert format_expr(state.expr) == "⊕"
    assert state.tier >= 3
    assert trace.steps
    assert Theta.T13.value == 13


def test_continuity_lineage_steps_have_parent_chain() -> None:
    state = evaluate_symbolic_program("Θ.⊙")

    assert state.lineage
    assert state.lineage[0].trace_id == state.trace_id
    assert state.lineage[0].parent_step is None
    assert state.lineage[1].parent_step == state.lineage[0].step_id
    assert state.lineage[1].transition_type == "rewrite"
    assert "inv:energy-bounded" in state.lineage[1].invariant_id


def test_promotion_paths_distinguish_stable_and_coherent() -> None:
    stable = evaluate_symbolic_program("⟲.2")
    coherent = evaluate_symbolic_program("⟲?")

    assert stable.lineage[-1].transition_type == "promotion:stable"
    assert coherent.lineage[-1].transition_type == "promotion:coherent"


def test_lineage_carries_decision_and_evidence_refs() -> None:
    vm = GovernedSymbolicVM(
        decision_ids=("dec:cab-eval-branch-3",),
        evidence_refs=("ev:test:symbolic-organism-vm",),
    )
    state = vm.evaluate("κ⊕.⊙℃")

    assert isinstance(state.lineage[0], ContinuityTraceStep)
    assert state.lineage[-1].decision_id == ("dec:cab-eval-branch-3",)
    assert state.lineage[-1].evidence_refs == ("ev:test:symbolic-organism-vm",)
    assert state.invariants["no_contradiction"] is True


def test_coherent_promotion_emits_coherence_receipt() -> None:
    vm = GovernedSymbolicVM(
        decision_ids=("dec:cab-eval-branch-3",),
        evidence_refs=("ev:receipt:123", "ev:test:rls-l1-04"),
    )
    state = vm.evaluate("⟲?")

    assert len(state.coherence_receipts) == 1
    receipt = state.coherence_receipts[0]
    assert isinstance(receipt, CoherenceReceipt)
    assert receipt.trace_id == state.trace_id
    assert receipt.step_id == state.lineage[-1].step_id
    assert receipt.promotion_type == "coherent"
    assert "inv:no-contradiction" in receipt.invariants_evaluated
    assert "inv:no-contradiction" in receipt.invariants_passed
    assert receipt.obligations_resolved == ("obl:no-unresolved-obligation",)
    assert receipt.evidence_refs == ("ev:receipt:123", "ev:test:rls-l1-04")
    assert receipt.decision_ref == "dec:cab-eval-branch-3"


def test_symbolic_vm_trace_is_continuity_shaped() -> None:
    state, trace = SymbolicVM().run(parse_program("Θ⊙"))

    assert format_expr(state.expr) == "⊕"
    assert trace.steps[-1]["transition_type"] == "rewrite"
    assert trace.steps[-1]["parent_step"] == trace.steps[0]["step_id"]
    assert "assumption_id" in trace.steps[-1]
