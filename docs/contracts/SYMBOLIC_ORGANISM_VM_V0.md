# Symbolic Organism VM v0

Status: executable local model

This contract turns the attached symbolic organism into a bounded computational
artifact. It is a local parser/evaluator for symbolic reasoning and simulation.
It is not a real-world authority engine and does not make binding decisions.

## Core

- Base alphabet: 14 symbolic instruction atoms.
- Theta table: `Theta0` through `Theta14` kind/type expansion.
- Execution: deterministic segment evaluation, arrow transitions, rewrite rules.
- Loop: `⟲` searches for a fixpoint; `⟲?` resolves through `⊕⁺`.
- Promotion: `⊕⁺` marks monotonic progress.
- Halt: `⬆` is the explicit terminal state.
- Energy: positive and negative glyphs update the bounded energy score.
- Audit: every evaluation step emits both an `EvaluationTrace` and a
  continuity-anchored `ContinuityTraceStep`.

## Runtime

Implementation:

```text
src/symbolic_organism/vm.py
```

Entry point:

```python
from src.symbolic_organism import evaluate_symbolic_program

state = evaluate_symbolic_program("κ⊕.⊙℃")
assert state.expr == "⊖⬡"
```

Structured API:

```python
from src.symbolic_organism import SymbolicVM
from src.symbolic_organism.parser import parse_program, format_expr

state, trace = SymbolicVM().run(parse_program("Θ⊙"))
assert format_expr(state.expr) == "⊕"
```

CLI:

```powershell
.\.venv\Scripts\python.exe -m src.symbolic_organism "κ⊕.⊙℃"
```

The CLI escapes glyphs by default for Windows console compatibility. Add
`--unicode` for raw glyph output in Unicode-capable terminals.

## Governance Invariants

The VM reports these local invariants:

- `energy_bounded`
- `promotion_monotonic`
- `theta13_not_downcast`
- `explicit_halt_when_halted`
- `trace_present`
- `no_contradiction`
- `no_unresolved_obligation`
- `rewrite_confluent`
- `theta_consistent`

## Continuity-Anchored Lineage

Every state transition also becomes a CAB-compatible lineage node:

```json
{
  "trace_id": "symtrace:...",
  "step_id": "symtrace:...:step:1",
  "parent_step": "symtrace:...:step:0",
  "expr": "⊕",
  "energy": 900,
  "tier": "TIER_300_PLUS",
  "halted": false,
  "transition_type": "rewrite",
  "assumption_id": ["asm:theta-typing-v1", "asm:rewrite-rules-v0"],
  "invariant_id": ["inv:no-contradiction", "inv:tier-monotonic"],
  "decision_id": [],
  "evidence_refs": [],
  "timestamp": 0
}
```

The `parent_step` chain makes the organism replayable as lineage, not just a
flat log.

## Promotion Paths

The VM distinguishes two promotion pathways:

- `promotion:stable`: emitted when a loop/fixpoint stops evolving.
- `promotion:coherent`: emitted when an explicit promotion operator resolves
  through coherence checks.

This keeps "stable" separate from "coherent"; a stable contradiction does not
automatically become coherent.

## Coherence Receipts

Every `promotion:coherent` emits a `CoherenceReceipt`:

```json
{
  "receipt_id": "coherence:...",
  "trace_id": "symtrace:...",
  "step_id": "symtrace:...:step:2",
  "promotion_type": "coherent",
  "invariants_evaluated": [
    "inv:no-contradiction",
    "inv:theta-consistent",
    "inv:rewrite-confluent",
    "inv:no-unresolved-obligation",
    "inv:energy-bounded"
  ],
  "invariants_passed": [
    "inv:no-contradiction",
    "inv:theta-consistent",
    "inv:rewrite-confluent"
  ],
  "obligations_resolved": ["obl:no-unresolved-obligation"],
  "evidence_refs": [],
  "decision_ref": "",
  "timestamp": "2026-06-19T00:00:00+00:00"
}
```

This completes the local chain:

```text
Execution -> Trace -> Lineage -> Coherence -> Receipt
```

## Test

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_symbolic_organism_vm.py -q
```
