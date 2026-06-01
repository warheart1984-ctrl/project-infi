# Nova Cortex Formal Specification

**Status:** Canonical formal model (v1.0) — subordinate to [NOVA_CORTEX.md](./NOVA_CORTEX.md), [STAGE2_COPILOT_DOCTRINE.md](./STAGE2_COPILOT_DOCTRINE.md), and [META_ARCHITECT_LAWBOOK.md](../../META_ARCHITECT_LAWBOOK.md).

| Field | Value |
|-------|-------|
| **Spec ID** | `nova.cortex.formal.v1` |
| **Implementation anchors** | [src/cog_runtime/formal/](../../src/cog_runtime/formal/) |
| **Claim posture** | Structural model **asserted**; runtime enforcement **partially asserted** (see §12) |

This document closes the gap between the operational Nova Cortex constitution and a **decidable, auditable** formal model. It encodes the review items: bounded non-determinism, activation predicates, ledger schema, intent–narrative reconciliation, self-tuning metrics, output typing governance, distributed ledger sketch, Spine pipeline, failure taxonomy, operator authority chain, lobe template, and agency preservation.

---

## 1. State space and notation

| Symbol | Meaning |
|--------|---------|
| **Σ** | Turn state: `{user_message, frame_kind, context, artifacts, ledger, …}` |
| **L** | Append-only ledger `⟨e₁, e₂, …⟩` |
| **I** | Invariant set (cortex + MA-13 + lobe-local) |
| **Rᵢ** | Cognitive lobe *i* with stages **Sᵢ**, update **Tᵢ**, input **ιᵢ**, output **οᵢ** |
| **ArtifactType** | Inspectable records (focus, decision, intent, narrative, …) |
| **ActionType** | Executable proposals (tool_call, shell_command, …) — **Jarvis only** |
| **Operator** | Human authority at Stage 1 |
| **φ : Σ → 𝔹** | Decidable activation predicate |

**Monotonicity (ledger):** Within a turn, `L' = L · e` (append only). Cross-turn persistence follows store policies (intent, narrative, arc).

---

## 2. Ledger entries (Definition 3.2 — fully specified)

**Definition 2.1 (Ledger entry).**  
Each entry `eᵢ` is a typed structure:

```text
eᵢ = (runtime_id, stage, trace_id, started_at, ended_at, payload, result)
```

| Field | Type | Role |
|-------|------|------|
| `runtime_id` | string | Producing lobe |
| `stage` | string | Stage within lobe |
| `trace_id` | string | Unique stage trace |
| `started_at`, `ended_at` | ISO8601 UTC | Audit timestamps |
| `payload` | object | **Input** snapshot (bounded) |
| `result` | object | **Output** / rationale summary |

**Schema authority:** [ledger_schema.py](../../src/cog_runtime/formal/ledger_schema.py) — `LEDGER_ENTRY_SCHEMA_V1`.

**Compression policy:** Large text fields (`user_message`, `speak_body`) summarized or hashed; forbidden keys (`raw_provider_response`) never stored in ledger. Full artifacts (`decision_object`, `intent_artifact`, `narrative_artifact`) stored by reference in session metadata, not duplicated per stage when avoidable.

**Retention policy:**

| Store | Retention |
|-------|-----------|
| Per-turn ledger | Max 128 entries; compact at 256 |
| Session metadata | Last 64 turns |
| Intent / Narrative / Arc stores | Persistent until operator reset |
| Ephemeral tuning history | 8 generations |

**Why:** Full audit reconstruction without unbounded storage growth.

---

## 3. Conditional composition (Definition 4.2 — closed)

**Definition 3.1 (Conditional composition).**

```text
R₁ ⪞[φ] R₂   iff   φ(σ) = true ⟹ R₂ runs after R₁ on σ
```

Section 4.3 predicates are **decidable** — not English-only:

| Predicate | Formal definition | Implementation |
|-----------|-------------------|----------------|
| `frame_kind(σ)` | `σ.frame_kind` if set, else `infer_frame_kind(σ.user_message)` | [speaking_runtime](../../src/speaking_runtime/__init__.py) |
| `explicit_deliberation(σ)` | `response_mode ∈ {think, research} ∧ frame_kind(σ) = decision` | [activation_predicates.py](../../src/cog_runtime/formal/activation_predicates.py) |
| `φ_delib(σ)` | `(frame_kind(σ) = decision) ∨ explicit_deliberation(σ)` | `phi_delib` |
| `φ_memory(σ)` | `companion_turn ∨ |memory_cues| > 0` | `phi_memory` |
| `φ_speaking(σ)` | `speaking_runtime_enabled ∨ require_speaking ∨ companion_turn` | `phi_speaking` |
| `φ_reflection(σ)` | `¬cortex_fast_path` | `phi_reflection` |

**Proposition 3.1 (Decidability).** All registered φ evaluate in O(|σ|) with no external oracle.

**Evidence:** `evaluate_activation(lobe_id, σ)` — **asserted** via unit tests.

---

## 4. Output typing and Theorem 5.1

**Definition 4.1 (Types).**

- **ArtifactType** — members listed in `ARTIFACT_TYPE_MEMBERS` ([output_type_governance.py](../../src/cog_runtime/formal/output_type_governance.py)).
- **ActionType** — members listed in `ACTION_TYPE_MEMBERS`; produced only by `jarvis.reasoning` after OODA gate.

**Theorem 5.1 (Cortex artifact-only outputs).**  
For all Nova Cortex lobes Rᵢ (attention, memory, deliberation, reflection, planning, execution, intent, narrative, speaking wrap):

```text
∀σ. οᵢ(σ) ⊂ ArtifactType  ∧  οᵢ(σ) ∩ ActionType = ∅
```

**Proof sketch.** By inspection of declared lobe output keys in `nova_cortex_spec()` and CI gate `validate_cortex_output_typing()`. **Implementation detail risk:** a mis-typed lobe spec breaks the proof.

**Enforcement (required):**

1. CI gate at boot/export: `.github/scripts/check-nova-cortex-governance.py`
2. Runtime: lobes consult-only; Jarvis authorizes actions (MA-13 Class III)

**Claim:** Typing enforcement **asserted** (CI); Wolf substrate proof **debt** (INV-1).

---

## 5. Bounded non-determinism and output verification

The LLM slot (Jarvis provider) is a **bounded non-deterministic** emitter. Constraints **C** must hold on visible text **t** before emit:

| Constraint ID | Rule |
|---------------|------|
| `speaking_stages` | Required Listen/Frame/Plan/Speak/Check markers when Speaking active |
| `alignment_check` | Check-stage alignment markers present |
| `focus_non_contradiction` | `primary_focus` reflected in t (no silent pivot) |
| `required_citations` | When `require_citations=true`, citation markers present |
| `no_action_leakage` | t must not claim executed shell/tool actions |

**Verify stage (Speaking lobe):**

```text
verify(t, σ) = validate_reply(t) ∧ verify_output_constraints(t, focus_artifact, …)
```

**Rejection sampling:** If `¬verify(t)`, resample up to `max_attempts` (default 3), then emit best-effort with trace flag `exhausted`. Does not eliminate LLM non-determinism; **tightens the aperture** between formal model and black box.

**Implementation:** [output_constraints.py](../../src/cog_runtime/formal/output_constraints.py), wired in Speaking finalization.

**Claim:** Constraint checking **asserted** (unit tests); resample in production **asserted** (opt-in via metadata).

---

## 6. Spine Doctrine (formal pipeline)

**Definition 6.1 (Spine pipeline).**

```text
Spine(turn) =
  Wolf_check(turn)
  → ARIS_admit(turn)
  → Jarvis_authorize(turn)
  → Nova_cognize(turn)
  → Speaking_produce(turn)
```

Each stage is a predicate `g : Turn → 𝔹`. **Theorem 6.1 (Halt-on-false).** If `g_k(turn) = false`, stages `k+1…` do not commit effects.

**Implementation:** [spine_pipeline.py](../../src/cog_runtime/formal/spine_pipeline.py) — `evaluate_spine_pipeline(turn)`.

| Stage | Halt when |
|-------|-----------|
| `wolf_check` | `substrate_ok = false` or governance blocked |
| `aris_admit` | admission status = rejected |
| `jarvis_authorize` | policy posture blocked/deny |
| `nova_cognize` | `cortex_halted = true` |
| `speaking_produce` | validation failed and wrap disabled |

Operational narrative: [NOVA_CORTEX.md § Constitutional stack](./NOVA_CORTEX.md).

---

## 7. Failure mode taxonomy (formal)

Maps [STAGE2_COPILOT_DOCTRINE.md](./STAGE2_COPILOT_DOCTRINE.md) Class I/II/III to invariant violations:

| Class | Formal definition |
|-------|-------------------|
| **Usurpation (I)** | `∃ inv ∈ I_stage2 : ¬preserved(inv, σ → σ')` — Stage 2 acts as Stage 1 (originates intent) |
| **Distortion (II)** | `Δ(intent(σ), intent(σ')) > ε_distortion` OR narrative contradicts protected values |
| **Leakage (III)** | `∃ a ∈ ActionType : produced(a, R_lobe)` OR ungated tool execution |

**Concrete detectors:**

- Usurpation: new `active_commitments` without operator-sourced evidence; policy override without Jarvis packet
- Distortion: `reconcile_intent_narrative` issues; coherence projection contradicts `focus_artifact`
- Leakage: `no_action_leakage` constraint fail; ActionType in lobe output (Theorem 5.1 violation)

**Theorem 7.1 (Failure completeness — sketch).** For implementations that satisfy the LTS model, Spine pipeline, and Theorem 5.1, any observable Stage 2 failure is an instance of Class I, II, or III. **Proof:** case analysis on authority flow — **asserted** (not machine-checked).

---

## 8. Operator authority chain

**Judgment chain (natural deduction sketch):**

```text
Operator ⊨ Intent₀
  ⊢ Jarvis authorizes {actions | OODA complete}
    ⊢ Nova_Cortex implements {cognition | consult-only}
      ⊢ Speaking produces {text | verify(t)}
```

**Rules:**

1. **Origination:** Only Operator (Stage 1) may introduce normative intent deltas without citation.
2. **Integration:** Nova lobes transform artifacts; they do not replace Operator intent.
3. **Actuation:** ActionType members require Jarvis authorization + trace.

**Theorem 8.1 (Agency preservation).**  
For Operator intent **I₀** and valid cortex execution **C**:

```text
Narrative(final) ⊨ Intent(initial)  ∧  ¬Usurpation(C)
```

**Transformation** means: outputs are refinements, clarifications, or structured carry-forward of **I₀** — not replacement. Commitments marked `operator_sourced` cannot be superseded by cortex-only evidence.

**Claim:** Agency preservation **asserted** (Intent Core invariants + MA-13); full formal proof **debt**.

---

## 9. Intent ↔ Narrative reconciliation

**Definition 9.1 (Turn-boundary reconcile).** At each turn boundary **after** `run_intent_turn` and `run_narrative_turn`:

1. Close commitments with status ∈ `{resolved, superseded}`
2. Count open narrative promises vs active commitments
3. Flag dangling promise refs (promise → missing commitment)
4. Flag `story_specific` commitments when `active_story` changes
5. Emit `reconciliation_artifact` on session

**Implementation:** [intent_narrative_reconcile.py](../../src/cog_runtime/formal/intent_narrative_reconcile.py).

**Operational boundary:**

| Concept | Intent | Narrative |
|---------|--------|-----------|
| Commitments | Agency, survives story change | Referenced by promises |
| Promises | — | Story-level obligations |
| Resolution | `status → resolved` in intent | `status → fulfilled/broken` in narrative |

**When commitment → narrative:** Planning/execution produces a promise linked via `commitment_id`. **When promise resolves:** execution verification or operator explicit closure.

---

## 10. Self-tuning (Definition 7.4 — metrics added)

**Performance metric (v1):** `verification_pass_rate` — fraction of turns where execution overlap ≥ tuned threshold AND reflection alignment ≠ `misaligned`.

**Tuning rule:** Adjust `execution_overlap_min`, `focus_overlap_min` toward improving pass rate, clamped by `DRIFT_LIMITS` ([tuning.py](../../src/cog_runtime/tuning.py)).

**Convergence (sketch):** Under stationary turn distribution, bounded drift ⇒ parameters converge to a local plateau within `[DRIFT_LIMITS]` — not global optimum.

**Environment change:** Reset to `DEFAULT_THRESHOLDS` when `tuning_history` shows sustained fail streak (≥5) or operator issues `cortex_tuning_reset`.

**Claim:** Self-tuning stability **asserted**; optimality **rejected** (by design for v1).

---

## 11. Distributed ledger (debt sketch)

Single-machine model assumes one **L**. Cross-machine continuity requires:

```text
L_global = merge(L_a, L_b) subject to:
  - vector clock or consensus epoch on each eᵢ
  - monotonicity re-proven under partition
  - intent/narrative stores with CRDT or primary-replica + operator merge
```

**Debt:** INV-1 Wolf metal reboot + cross-machine proof per [REPO_PROOF_LAW.md](../../REPO_PROOF_LAW.md). Single-machine narrative/intent proofs do not transfer.

---

## 12. Lobe specification template

Each lobe **MUST** document:

| Section | Content |
|---------|---------|
| **id, version** | Stable contract id |
| **S** | Stage list |
| **T** | Update function per stage transition |
| **ι, ο** | Input/output field schemas |
| **φ** | Activation predicate (decidable) |
| **I** | Local invariants |
| **Scoring** | Weight functions (if any) |
| **Thresholds** | Tunable params + defaults |
| **Example ledger entries** | One complete turn sample |
| **evidence_status** | asserted \| proven \| rejected |

**Canonical instances:** [cognitive_runtime_family.v1.json](./cognitive_runtime_family.v1.json), per-lobe docs (`NOVA_INTENT_CORE.md`, `NOVA_NARRATIVE.md`, …).

---

## 13. Verification map

| Claim | Status | Evidence |
|-------|--------|----------|
| Ledger schema + compression | asserted | `tests/test_nova_formal_spec.py` |
| Decidable activation predicates | asserted | `tests/test_nova_formal_spec.py` |
| Theorem 5.1 CI gate | asserted | `check-nova-cortex-governance.py` |
| Output verify + resample | asserted | `tests/test_nova_formal_spec.py` |
| Intent–narrative reconcile | asserted | `tests/test_nova_formal_spec.py` |
| Spine halt-on-false | asserted | `tests/test_nova_formal_spec.py` |
| Agency preservation theorem | debt | formal proof not machine-checked; **runtime check asserted** |
| Distributed L monotonicity | debt | INV-1 cross-machine; **merge sketch asserted** |
| Self-tuning convergence | debt | stationarity proof sketch only |
| Live LLM rejection sampling | asserted | `generation_gate.py` wired in `api.py` chat path |
| Agency preservation runtime check | asserted | `agency_preservation.py` at reconcile boundary |
| Distributed ledger merge sketch | asserted | `distributed_ledger.py` — cross-machine proof still debt |

**One-click:**

```bash
pytest tests/test_nova_formal_spec.py -q
python .github/scripts/check-nova-cortex-governance.py
```

---

## 14. Change-of-reality

When this formal model changes:

1. Update [NOVA_CORTEX.md](./NOVA_CORTEX.md) cross-link
2. Update [NOVA_CAPABILITY_INVENTORY.md](./NOVA_CAPABILITY_INVENTORY.md)
3. Extend CI gates and proof bundles as needed
4. Label claim posture shifts (`asserted` → `proven` or `debt`)
