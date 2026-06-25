"""Bounded VM for the governed symbolic organism.

The runtime implements the concrete computational surface from the attached
symbol stack: a base-14 glyph alphabet, theta-kind expansion, rewrite
morphisms, loop promotion, energy tiers, and explicit halt.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
import time
from typing import Any, Iterable, TypeAlias
from uuid import uuid4


SEED = "⊙"
POSITIVE = "⊕"
NEGATIVE = "⊖"
LOOP = "⟲"
PROMOTION = "⊕⁺"
HALT = "⬆"
ARROW = "→"


BASE14_ALPHABET: dict[int, dict[str, str]] = {
    0: {"symbol": "⊙", "role": "seed/null-state"},
    1: {"symbol": "β", "role": "first-order transform"},
    2: {"symbol": "κ", "role": "dual-branch selector"},
    3: {"symbol": "⊕", "role": "positive bit/promote"},
    4: {"symbol": "ψ", "role": "expansion operator"},
    5: {"symbol": "Θ", "role": "type lift"},
    6: {"symbol": "λρδγφξ", "role": "multi-emitter"},
    7: {"symbol": "⬄", "role": "reversible op"},
    8: {"symbol": "ℏτ", "role": "nondeterministic branch"},
    9: {"symbol": "e⁻", "role": "negative charge"},
    10: {"symbol": "♀", "role": "generative node"},
    11: {"symbol": "◆", "role": "stable fixed-point"},
    12: {"symbol": "⚜", "role": "high-order marker"},
    13: {"symbol": "⟡≈", "role": "approximation boundary"},
}


THETA_LAYERS: dict[int, dict[str, str]] = {
    0: {"symbol": "⊙", "role": "seed type"},
    1: {"symbol": "κ⊕", "role": "dual-charge type"},
    2: {"symbol": "⟐", "role": "hinge type"},
    3: {"symbol": "⊢", "role": "gate type"},
    4: {"symbol": "↔", "role": "bidirectional type"},
    5: {"symbol": "⟡", "role": "facet type"},
    6: {"symbol": "◆", "role": "stable-core type"},
    7: {"symbol": "Θ", "role": "self-reference type"},
    8: {"symbol": "λ", "role": "emission type"},
    9: {"symbol": "⊕", "role": "positive type"},
    10: {"symbol": "◇", "role": "diamond type"},
    11: {"symbol": "κ⊕", "role": "dual-charge repeat"},
    12: {"symbol": "⊙⃡", "role": "rotating seed type"},
    13: {"symbol": "∞", "role": "infinite-extension type"},
    14: {"symbol": "⊙", "role": "seed return type"},
}


COMPOSITE_THETA: dict[str, tuple[int, ...]] = {
    "⊙": (0, 1, 14),
    "κ⊕": (11, 3),
    "Θ": (7, 8),
    "♀": (6, 9),
    "σ≈": (4, 13),
}


DEFAULT_REWRITE_RULES: tuple[tuple[str, str, str], ...] = (
    ("κ⊕.⊙℃", "⊖⬡", "thermal dual-charge collapses to negative facet"),
    ("κ⊕⊙℃", "⊖⬡", "thermal dual-charge collapses to negative facet"),
    ("♀.⊕", "⊖⟨", "generative positive yields guarded negative entry"),
    ("♀⊕", "⊖⟨", "generative positive yields guarded negative entry"),
    ("Θ.⊙", "⊕", "self-reference seed canonicalizes to positive"),
    ("Θ⊙", "⊕", "self-reference seed canonicalizes to positive"),
    ("⟲?", "⊕⁺", "loop query resolves through promotion"),
    ("◇", "⊕", "diamond resolves to positive bit"),
    ("↺", "⬆", "return motion yields halt"),
    ("⊙℃", "⟦", "thermal seed opens bounded transition"),
    ("⊕⊗", "⬆", "positive tensor yields halt"),
)


ENERGY_DELTAS: dict[str, int] = {
    "⊕": 900,
    "⊕⁺": 1080,
    "⊖": -2000,
}


TIER_BOUNDS: tuple[tuple[str, int, int | None], ...] = (
    ("TIER_0_25", 0, 25),
    ("TIER_25_100", 25, 100),
    ("TIER_100_300", 100, 300),
    ("TIER_300_PLUS", 300, None),
)


class Theta(Enum):
    """Theta-kind indices used by the symbolic organism."""

    T0 = 0
    T1 = 1
    T2 = 2
    T3 = 3
    T4 = 4
    T5 = 5
    T6 = 6
    T7 = 7
    T8 = 8
    T9 = 9
    T10 = 10
    T11 = 11
    T12 = 12
    T13 = 13
    T14 = 14


@dataclass(frozen=True)
class Symbol:
    """A glyph plus optional theta annotations."""

    glyph: str
    thetas: tuple[Theta, ...] = field(default_factory=tuple)

    def __str__(self) -> str:
        if not self.thetas:
            return self.glyph
        indices = ".".join(str(theta.value) for theta in self.thetas)
        return f"{self.glyph}.{indices}"


Expr: TypeAlias = list[Symbol]


@dataclass
class State:
    """Compatibility state for the SymbolicVM API."""

    expr: Expr
    energy: int = 0
    tier: int = 0
    halted: bool = False
    promoted: bool = False
    invariants: dict[str, bool] = field(default_factory=dict)


@dataclass
class ExecutionTrace:
    """JSON-friendly execution trace for the SymbolicVM API."""

    steps: list[dict[str, Any]] = field(default_factory=list)

    def record(self, state: State, note: str) -> None:
        self.steps.append(
            {
                "expr": "".join(symbol.glyph for symbol in state.expr),
                "energy": state.energy,
                "tier": state.tier,
                "halted": state.halted,
                "promoted": state.promoted,
                "invariants": dict(state.invariants),
                "note": note,
            }
        )


@dataclass(frozen=True)
class ContinuityTraceStep:
    """CAB-compatible lineage node for one symbolic transition."""

    trace_id: str
    step_id: str
    parent_step: str | None
    expr: str
    energy: int
    tier: str
    halted: bool
    transition_type: str
    assumption_id: tuple[str, ...] = field(default_factory=tuple)
    invariant_id: tuple[str, ...] = field(default_factory=tuple)
    decision_id: tuple[str, ...] = field(default_factory=tuple)
    evidence_refs: tuple[str, ...] = field(default_factory=tuple)
    timestamp: int = 0

    def to_dict(self) -> dict[str, object]:
        return {
            "trace_id": self.trace_id,
            "step_id": self.step_id,
            "parent_step": self.parent_step,
            "expr": self.expr,
            "energy": self.energy,
            "tier": self.tier,
            "halted": self.halted,
            "transition_type": self.transition_type,
            "assumption_id": list(self.assumption_id),
            "invariant_id": list(self.invariant_id),
            "decision_id": list(self.decision_id),
            "evidence_refs": list(self.evidence_refs),
            "timestamp": self.timestamp,
        }


@dataclass(frozen=True)
class CoherenceReceipt:
    """Auditable proof artifact emitted by coherent promotion."""

    receipt_id: str
    trace_id: str
    step_id: str
    promotion_type: str
    invariants_evaluated: tuple[str, ...]
    invariants_passed: tuple[str, ...]
    obligations_resolved: tuple[str, ...] = field(default_factory=tuple)
    evidence_refs: tuple[str, ...] = field(default_factory=tuple)
    decision_ref: str = ""
    timestamp: str = ""

    def to_dict(self) -> dict[str, object]:
        return {
            "receipt_id": self.receipt_id,
            "trace_id": self.trace_id,
            "step_id": self.step_id,
            "promotion_type": self.promotion_type,
            "invariants_evaluated": list(self.invariants_evaluated),
            "invariants_passed": list(self.invariants_passed),
            "obligations_resolved": list(self.obligations_resolved),
            "evidence_refs": list(self.evidence_refs),
            "decision_ref": self.decision_ref,
            "timestamp": self.timestamp,
        }


@dataclass(frozen=True)
class EvaluationTrace:
    """One auditable VM step."""

    step: int
    op: str
    before: str
    after: str
    detail: str = ""
    energy: int = 0
    tier: str = "TIER_0_25"


@dataclass
class SymbolicState:
    """Current VM state."""

    expr: str = ""
    energy: int = 0
    tier: str = "TIER_0_25"
    halted: bool = False
    promoted: bool = False
    trace_id: str = ""
    trace: list[EvaluationTrace] = field(default_factory=list)
    lineage: list[ContinuityTraceStep] = field(default_factory=list)
    coherence_receipts: list[CoherenceReceipt] = field(default_factory=list)
    invariants: dict[str, bool] = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        return {
            "expr": self.expr,
            "energy": self.energy,
            "tier": self.tier,
            "halted": self.halted,
            "promoted": self.promoted,
            "trace_id": self.trace_id,
            "invariants": dict(self.invariants),
            "trace": [trace.__dict__ for trace in self.trace],
            "lineage": [step.to_dict() for step in self.lineage],
            "coherence_receipts": [receipt.to_dict() for receipt in self.coherence_receipts],
        }


class GovernedSymbolicVM:
    """A deterministic, bounded rewrite VM for the symbolic organism."""

    def __init__(
        self,
        rewrite_rules: Iterable[tuple[str, str, str]] = DEFAULT_REWRITE_RULES,
        max_energy_abs: int = 35_350,
        assumption_ids: Iterable[str] = ("asm:theta-typing-v1", "asm:rewrite-rules-v0"),
        invariant_ids: Iterable[str] = (
            "inv:no-contradiction",
            "inv:tier-monotonic",
            "inv:energy-bounded",
            "inv:theta-consistent",
            "inv:rewrite-confluent",
            "inv:no-unresolved-obligation",
        ),
        decision_ids: Iterable[str] = (),
        evidence_refs: Iterable[str] = (),
    ) -> None:
        self.rewrite_rules = tuple(rewrite_rules)
        self.max_energy_abs = max_energy_abs
        self.assumption_ids = tuple(assumption_ids)
        self.invariant_ids = tuple(invariant_ids)
        self.decision_ids = tuple(decision_ids)
        self.evidence_refs = tuple(evidence_refs)

    def theta_expand(self, symbol: str) -> tuple[int, ...]:
        """Return theta indices for a known symbol or typed reference."""

        symbol = self._clean_atom(symbol)
        if symbol in COMPOSITE_THETA:
            return COMPOSITE_THETA[symbol]
        if symbol.startswith("Θ"):
            suffix = symbol[1:]
            if suffix and all(part.isdigit() for part in suffix.split(".") if part):
                return tuple(int(part) for part in suffix.split(".") if part)
        for index, spec in THETA_LAYERS.items():
            if spec["symbol"] == symbol:
                return (index,)
        return ()

    def numeric_sequence(self, program: str) -> tuple[int, ...]:
        """Resolve any base-14 symbols in a program into numeric indices."""

        symbols = {spec["symbol"]: index for index, spec in BASE14_ALPHABET.items()}
        found: list[int] = []
        for atom in self._atoms(program):
            atom = self._clean_atom(atom)
            if atom in symbols:
                found.append(symbols[atom])
        return tuple(found)

    def evaluate(self, program: str, max_steps: int = 128) -> SymbolicState:
        state = SymbolicState(trace_id=f"symtrace:{uuid4()}")
        segments = [segment.strip() for segment in program.split("|") if segment.strip()]
        if not segments:
            self._refresh_invariants(state)
            return state

        for segment in segments:
            if len(state.trace) >= max_steps or state.halted:
                break
            self._eval_segment(segment, state, max_steps)

        self._refresh_invariants(state)
        return state

    def _eval_segment(self, segment: str, state: SymbolicState, max_steps: int) -> None:
        segment = self._clean_atom(segment)
        if not segment:
            return
        if ARROW in segment:
            self._eval_transition_chain(segment, state)
            return
        if segment.startswith(f"{LOOP}."):
            self._eval_loop(segment, state, max_steps)
            return
        self._set_expr(segment, state, "read", "loaded segment")
        self._apply_rewrites(state, max_steps=max_steps)

    def _eval_transition_chain(self, segment: str, state: SymbolicState) -> None:
        parts = [self._clean_atom(part) for part in segment.split(ARROW) if part.strip()]
        if not parts:
            return
        if not state.expr:
            self._set_expr(parts[0], state, "read", "transition source")
            targets = parts[1:]
        else:
            targets = parts[1:] if parts[0] == state.expr else parts
        for target in targets:
            canonical = self._canonical_target(target)
            self._set_expr(canonical, state, "transition", f"{segment}")
            self._apply_rewrites(state)
            if state.halted:
                break

    def _eval_loop(self, segment: str, state: SymbolicState, max_steps: int) -> None:
        try:
            count = int(segment.split(".", 1)[1])
        except ValueError:
            count = 1
        count = max(0, min(count, max_steps))
        for _ in range(count):
            before = state.expr
            self._apply_rewrites(state, max_steps=max_steps)
            if state.expr == before:
                self._promote(state, "loop reached fixpoint", promotion_kind="stable")
                break

    def _apply_rewrites(self, state: SymbolicState, max_steps: int = 128) -> None:
        for _ in range(max_steps):
            changed = False
            for pattern, replacement, detail in self.rewrite_rules:
                if state.expr == pattern:
                    self._set_expr(replacement, state, "rewrite", detail)
                    changed = True
                    break
            if state.expr == PROMOTION:
                self._promote(state, "promotion operator", promotion_kind="coherent")
            if state.expr == HALT:
                state.halted = True
            if not changed:
                break

    def _promote(self, state: SymbolicState, detail: str, promotion_kind: str) -> None:
        if state.promoted:
            return
        before = state.expr
        state.promoted = True
        state.expr = PROMOTION
        self._adjust_energy(state, PROMOTION)
        self._append_trace(state, f"promotion:{promotion_kind}", before, state.expr, detail)

    def _set_expr(self, expr: str, state: SymbolicState, op: str, detail: str) -> None:
        before = state.expr
        state.expr = self._canonical_target(expr)
        self._adjust_energy(state, state.expr)
        if state.expr == HALT:
            state.halted = True
        self._append_trace(state, op, before, state.expr, detail)

    def _adjust_energy(self, state: SymbolicState, expr: str) -> None:
        remaining = expr
        for symbol, delta in sorted(ENERGY_DELTAS.items(), key=lambda item: len(item[0]), reverse=True):
            count = remaining.count(symbol)
            if count:
                state.energy += delta * count
                remaining = remaining.replace(symbol, "")
        state.tier = self._tier_for_energy(state.energy)

    def _tier_for_energy(self, energy: int) -> str:
        magnitude = abs(energy)
        for name, lower, upper in TIER_BOUNDS:
            if magnitude >= lower and (upper is None or magnitude < upper):
                return name
        return "TIER_300_PLUS"

    def _append_trace(
        self,
        state: SymbolicState,
        op: str,
        before: str,
        after: str,
        detail: str = "",
    ) -> None:
        state.trace.append(
            EvaluationTrace(
                step=len(state.trace),
                op=op,
                before=before,
                after=after,
                detail=detail,
                energy=state.energy,
                tier=state.tier,
            )
        )
        state.lineage.append(
            ContinuityTraceStep(
                trace_id=state.trace_id,
                step_id=f"{state.trace_id}:step:{len(state.lineage)}",
                parent_step=state.lineage[-1].step_id if state.lineage else None,
                expr=after,
                energy=state.energy,
                tier=state.tier,
                halted=state.halted,
                transition_type=self._transition_type(op, after),
                assumption_id=self.assumption_ids,
                invariant_id=self.invariant_ids,
                decision_id=self.decision_ids,
                evidence_refs=self.evidence_refs,
                timestamp=time.time_ns(),
            )
        )
        if op == "promotion:coherent":
            state.coherence_receipts.append(self._build_coherence_receipt(state, state.lineage[-1]))

    def _refresh_invariants(self, state: SymbolicState) -> None:
        state.invariants = {
            "energy_bounded": abs(state.energy) <= self.max_energy_abs,
            "promotion_monotonic": not state.promoted or state.energy > 0,
            "theta13_not_downcast": not self._has_forbidden_theta13_downcast(state.trace),
            "explicit_halt_when_halted": not state.halted or state.expr == HALT,
            "trace_present": bool(state.trace),
            "no_contradiction": self._has_no_contradiction(state.expr),
            "no_unresolved_obligation": "?" not in state.expr,
            "rewrite_confluent": not self._has_pending_rewrite(state.expr),
            "theta_consistent": self._theta_consistent(state.expr),
        }

    def is_coherent(self, expr: str, state: SymbolicState | None = None) -> bool:
        """Return whether an expression satisfies the VM's coherence checks."""

        return all(self._coherence_results(expr, state).values())

    def _build_coherence_receipt(
        self,
        state: SymbolicState,
        step: ContinuityTraceStep,
    ) -> CoherenceReceipt:
        results = self._coherence_results(step.expr, state)
        passed = tuple(invariant for invariant, ok in results.items() if ok)
        obligations = ("obl:no-unresolved-obligation",) if results["inv:no-unresolved-obligation"] else ()
        return CoherenceReceipt(
            receipt_id=f"coherence:{uuid4()}",
            trace_id=step.trace_id,
            step_id=step.step_id,
            promotion_type="coherent",
            invariants_evaluated=tuple(results),
            invariants_passed=passed,
            obligations_resolved=obligations,
            evidence_refs=self.evidence_refs,
            decision_ref=self.decision_ids[0] if self.decision_ids else "",
            timestamp=datetime.now(UTC).isoformat(),
        )

    def _coherence_results(
        self,
        expr: str,
        state: SymbolicState | None = None,
    ) -> dict[str, bool]:
        energy = state.energy if state else 0
        return {
            "inv:no-contradiction": self._has_no_contradiction(expr),
            "inv:theta-consistent": self._theta_consistent(expr),
            "inv:rewrite-confluent": not self._has_pending_rewrite(expr),
            "inv:no-unresolved-obligation": "?" not in expr,
            "inv:energy-bounded": abs(energy) <= self.max_energy_abs,
        }

    def _has_forbidden_theta13_downcast(self, trace: Iterable[EvaluationTrace]) -> bool:
        for item in trace:
            before_theta = set(self.theta_expand(item.before))
            after_theta = set(self.theta_expand(item.after))
            if 13 in before_theta and after_theta and 13 not in after_theta:
                return True
        return False

    def _has_no_contradiction(self, expr: str) -> bool:
        return "⊕⊖" not in expr and "⊖⊕" not in expr

    def _has_pending_rewrite(self, expr: str) -> bool:
        return any(expr == pattern for pattern, _, _ in self.rewrite_rules)

    def _theta_consistent(self, expr: str) -> bool:
        return not ("Θ13" in expr and "Θ0" in expr)

    def _transition_type(self, op: str, after: str) -> str:
        if after == HALT:
            return "halt"
        if op in {"rewrite", "promotion:stable", "promotion:coherent"}:
            return op
        if op == "transition":
            return "coherence-lift"
        return op

    def _atoms(self, program: str) -> tuple[str, ...]:
        atoms: list[str] = []
        for segment in program.replace(ARROW, "|").replace("=", "|").split("|"):
            for part in segment.split("."):
                atom = self._clean_atom(part)
                if atom:
                    atoms.append(atom)
        return tuple(atoms)

    def _canonical_target(self, expr: str) -> str:
        expr = self._clean_atom(expr)
        if "=" in expr:
            return self._clean_atom(expr.split("=")[-1])
        if expr.startswith("="):
            return self._clean_atom(expr[1:])
        return expr

    def _clean_atom(self, value: str) -> str:
        return (
            value.strip()
            .replace(" ", "")
            .replace("[1][1][1][1]", "⊕⊕⊕⊕")
            .replace("☐0-13", "☐0-13")
        )


class SymbolicVM:
    """Compatibility facade around GovernedSymbolicVM.

    The facade accepts and returns structured `Expr` values while the core VM
    keeps the richer string-based transition trace used by the CLI and contract.
    """

    def __init__(self, max_steps: int = 1024) -> None:
        self.max_steps = max_steps
        self._vm = GovernedSymbolicVM()

    @staticmethod
    def expr_to_string(expr: Expr) -> str:
        return "".join(symbol.glyph for symbol in expr)

    @staticmethod
    def string_to_expr(value: str) -> Expr:
        return [Symbol(glyph) for glyph in value if not glyph.isspace()]

    @staticmethod
    def tier_for_energy(energy: int) -> int:
        magnitude = abs(energy)
        if magnitude < 25:
            return 0
        if magnitude < 100:
            return 1
        if magnitude < 300:
            return 2
        return 3

    def run(self, initial: Expr) -> tuple[State, ExecutionTrace]:
        initial_text = self.expr_to_string(initial)
        evaluated = self._vm.evaluate(initial_text, max_steps=self.max_steps)
        state = State(
            expr=self.string_to_expr(evaluated.expr),
            energy=evaluated.energy,
            tier=self.tier_for_energy(evaluated.energy),
            halted=evaluated.halted,
            promoted=evaluated.promoted,
            invariants=dict(evaluated.invariants),
        )
        trace = ExecutionTrace()
        lineage_by_expr_step = {index: step for index, step in enumerate(evaluated.lineage)}
        for index, item in enumerate(evaluated.trace):
            continuity_step = lineage_by_expr_step.get(index)
            payload = continuity_step.to_dict() if continuity_step else {}
            payload.update(
                {
                    "expr": item.after,
                    "energy": item.energy,
                    "tier": self.tier_for_energy(item.energy),
                    "halted": item.after == HALT,
                    "promoted": item.after == PROMOTION,
                    "note": item.detail or item.op,
                }
            )
            trace.steps.append(payload)
        if not trace.steps:
            trace.record(state, "start")
        return state, trace


def evaluate_symbolic_program(program: str, max_steps: int = 128) -> SymbolicState:
    """Evaluate a symbolic program with the default governed VM."""

    return GovernedSymbolicVM().evaluate(program, max_steps=max_steps)
