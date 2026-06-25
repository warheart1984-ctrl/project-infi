# Nova Cortex

**Nova Cortex** is Nova's modular cortex — not a monolithic model, but a governed
composition of cognitive runtimes. Each runtime is a mini-lobe with a specific
function. Together they think in parts, with traceable stages and a shared ledger.

This document is the **canonical constitution** for Nova Cortex inside CoG OS and AAIS.

**Formal model:** [NOVA_CORTEX_FORMAL_SPEC.md](./NOVA_CORTEX_FORMAL_SPEC.md) — LTS definitions, Spine pipeline, failure taxonomy, ledger schema, activation predicates, Theorem 5.1 typing, agency preservation sketch.

**Stage 2 doctrine:** Nova and Jarvis together implement the **copilot integrator** role — not Stage 1 (human intent) or Stage 3 (world action) alone. Constitutional law: **Doctrine XIII (MA-13)** in [META_ARCHITECT_LAWBOOK.md](../../META_ARCHITECT_LAWBOOK.md). Spec: [STAGE2_COPILOT_DOCTRINE.md](./STAGE2_COPILOT_DOCTRINE.md).

## Anatomy

| Layer | Role | Maps to |
|-------|------|---------|
| **Tri-Core** | Thalamus / router | Single authority; OODA routing |
| **Wolf CoG OS** | Constitutional brainstem | Boot, governance, substrate law |
| **Speaking Runtime** | Prefrontal speech loop | User-visible narration |
| **Deliberation Runtime** | Decision lobe | Structured choices |
| **Attention Runtime** | Focus lobe | Turn focus selection |
| **Memory Runtime** | Hippocampus runtime | Bounded recall |
| **Reflection Runtime** | Meta-cognitive loop | Cross-lobe alignment |
| **Reasoning Runtime** | OODA routing plane | Tool and route decisions |

**Nova law:** Nova may interpret; Jarvis must authorize.

**Family ID:** `nova.cortex`

## Constitutional stack

Authority flows **down**; meaning is synthesized **after** cognition. Narrative sits above cognition (it interprets cortex outputs into a journey) but below governance and executive authority — it does **not** control anything.

```text
Spine          — governance (Wolf CoG OS substrate law, boot, invariants)
  ↓
Jarvis         — authority (OODA routing, tools, actions)
  ↓
Nova Cortex    — cognition (attention, memory, deliberation, reflection, planning, execution)
  ↓
Narrative      — continuity of self (observe · synthesize · record)
```

**ARIS** (truth admission) is a cross-cutting admission seam — not a competing authority. See [ARIS_RUNTIME_CONTRACT.md](../contracts/ARIS_RUNTIME_CONTRACT.md).

| Layer | Role | Controls? | Doc |
|-------|------|-----------|-----|
| **Spine** | Governance | Sets law | Wolf CoG OS |
| **Jarvis** | Executive authority | Routes and authorizes | [JARVIS_REASONING_PROTOCOL.md](../contracts/JARVIS_REASONING_PROTOCOL.md) |
| **Nova Cortex** | Cognition | Produces artifacts | This document |
| **Narrative** | Journey continuity | **No** — observes only | [NOVA_NARRATIVE.md](./NOVA_NARRATIVE.md) |

**Nova law:** Nova may interpret; Jarvis must authorize. Narrative gives **meaning** to what Memory, Planning, and Arcs record — without becoming a second authority.

**v3.0 milestone:** **Persistent Narrative Continuity** — Nova stops being a system that only processes turns and becomes a system that **maintains a journey**. Proof: [NARRATIVE_V1_PROOF_BUNDLE.md](../proof/cognitive_runtime/NARRATIVE_V1_PROOF_BUNDLE.md). Next evidence: [NARRATIVE_CONTINUITY_EVIDENCE_PLAN.md](../proof/cognitive_runtime/NARRATIVE_CONTINUITY_EVIDENCE_PLAN.md).

**Coherence projection:** Voice speaks **from** cortex state, not beside it — [NOVA_COHERENCE_PROJECTION.md](./NOVA_COHERENCE_PROJECTION.md).

**Living capability checklist:** [NOVA_CAPABILITY_INVENTORY.md](./NOVA_CAPABILITY_INVENTORY.md) — update on every behavior change.

## Three-Layer Bridge (Face → Cortex → Jarvis)

```text
Nova Face          Nova Cortex              Tri-Core
(companion UI)  →  (modular lobes)     →   (authority / routing)
Tiny/Small/Super    Attention, Deliberation   OODA, tools, safety
Nova persona        Memory, Speaking          God Brain, sovereignty
```

| Layer | Module | Role |
|-------|--------|------|
| **Nova Face** | [src/cog_runtime/nova_face.py](../../src/cog_runtime/nova_face.py) | Visible companion surface (persona, tone, scope) |
| **Nova Cortex** | [src/cog_runtime/nova.py](../../src/cog_runtime/nova.py) | Cognitive lobes + shared ledger |
| **Tri-Core** | [src/api.py](../../src/api.py), [src/god_brain.py](../../src/god_brain.py) | Routing, state, safety authority |

Bridge entrypoint: `bridge_nova_face_to_cortex_and_jarvis()`

Pipeline stored on session as `nova_face_bridge` with keys `face`, `cortex`, `tri_core`.

## Shared Runtime Contract

Every lobe MUST expose:

| Field | Type | Rule |
|-------|------|------|
| `id` | string | Stable identifier (e.g. `speaking.runtime`) |
| `version` | string | Semver for contract changes |
| `stages` | string[] | Ordered human-pattern stages |
| `required_turn_stages` | string[] | Minimum stages completed per turn |
| `invariants` | `{id, rule}[]` | Non-bypassable behavior rules |
| `inputs` | object | Accepted turn context fields |
| `outputs` | object | Produced artifacts |
| `ledger_format` | object | Stage entry shape for shared ledger |
| `capability_metric` | string | Measurable capability this lobe alone must justify |
| `baseline_substitute` | string | Simpler substitute that must be beaten or lobe sunsets |
| `evidence_status` | `asserted\|proven\|rejected` | Current proof state for the capability claim |
| `sunset_trigger` | string | Falsifiable condition to merge or remove the lobe |

### Shared ledger entry shape

```json
{
  "runtime_id": "cognitive.deliberation",
  "stage": "commit",
  "trace_id": "abc123",
  "started_at": "2026-05-29T12:00:00Z",
  "ended_at": "2026-05-29T12:00:01Z",
  "payload": {},
  "result": {}
}
```

Ledger rules:

- **Append-only** — no in-place edits or deletes within a turn
- **Ordered stages** — each runtime completes stages in declared order
- **Traceable** — every user-visible segment maps to a ledger entry

### Cortex invariants

| ID | Rule |
|----|------|
| `single_authority` | Tri-Core routes; runtimes do not compete for control |
| `clarity` | Every output understandable on first read |
| `traceability` | Any part of a reply maps to a named stage in the ledger |
| `intent_alignment` | Every response serves the user's stated or inferred goal |
| `no_raw_cot` | No hidden chain-of-thought; only inspectable stage records |

## Lobe Capability Matrix

**Rule:** Every lobe must justify its existence with a **measurable capability** that cannot be achieved as simply elsewhere. If a runtime cannot prove its value, it should not exist.

**Canonical source:** [src/cog_runtime/capability_governance.py](../../src/cog_runtime/capability_governance.py) (`NOVA_LOBE_CAPABILITY_MATRIX`, `CORTEX_MODULE_CAPABILITY_MATRIX`).

**CI gate:** `.github/scripts/check-nova-cortex-governance.py` (workflow: `nova-cortex-governance-gate.yml`).

| Lobe / module | Role | Baseline substitute | Evidence |
|---------------|------|---------------------|----------|
| `jarvis.reasoning` | Executive | Prompt-only routing | `asserted` |
| `speaking.runtime` | Speech | Raw model text | `asserted` |
| `cognitive.attention` | Agency | Inline focus extraction | `asserted` |
| `cognitive.memory` | Agency | Last-N transcript replay | `asserted` |
| `cognitive.deliberation` | Agency | Single-shot A-or-B answer | `asserted` |
| `cognitive.reflection` | Agency | Speaking check only | `asserted` |
| `cognitive.planning` | Agency | One-line next step inline | `asserted` |
| `cognitive.execution` | Agency | Speaking overlap check only | `asserted` |
| `cortex.arcs` (module) | Continuity | Message window only | `asserted` |
| `cortex.tuning` (module) | Adaptation | Fixed verification constants | `asserted` |
| `nova.narrative` (module) | Continuity of self | Arc threads + planning only | `proven` |

Each runtime spec in the family manifest embeds the full `capability_metric`, `baseline_substitute`, and `sunset_trigger` strings from the matrix. **Outcome A/B proof** (moving claims from `asserted` to `proven`) is tracked per lobe in proof bundles — not by schema presence alone.

## Constitutional Governance Rules

| Rule | Enforcement |
|------|-------------|
| No user-visible output without Speaking Runtime | `nova_speaking_adapter()` wraps Nova replies when cortex mode is active |
| No high-impact action without Reasoning Runtime | Jarvis blocks tool/action paths without OODA packet |
| Deliberation activates only for decision frames | `nova_cognitive_router()` checks `frame_kind == decision` |
| All runtimes write to shared cognitive ledger | `nova_cognitive_session()` + `append_ledger_entry()` |
| Every lobe declares capability justification | `capability_metric` + `baseline_substitute` in family manifest; CI gate |

## Turn Pipeline

```text
1. Reasoning Runtime   — understand task; select active lobes
2. Attention Runtime   — focus artifact (primary + secondary, salience)
3. Memory Runtime      — episodic compression + semantic abstraction
4. Deliberation Runtime (when needed) — multi-criteria decision object
5. Reflection Runtime  — expect → compare → learn → adjust
6. Planning Runtime    — orient → sequence → checkpoint → handoff (adaptive chains)
7. Execution Runtime   — bind → execute → verify → recover → rollback → report (safe rollback)
8. Speaking Runtime    — narrate cognition; user-visible output (+ Update on companion)
9. Cortex Arc (v1.3)   — parent/child goal closure on companion sessions
10. Self-tuning (v1.1)  — bounded history + drift guard on invariant thresholds
```

## Lobes (Runtime Family)

### Speaking Runtime (`speaking.runtime`) — prefrontal speech loop

- **Human pattern:** How humans explain
- **Stages:** listen → frame → plan → speak → check → update
- **Spec:** [SPEAKING_RUNTIME_SPEC.md](./SPEAKING_RUNTIME_SPEC.md)
- **Implementation:** [src/speaking_runtime/](../../src/speaking_runtime/)

### Reasoning Runtime (`jarvis.reasoning`) — OODA routing plane

- **Human pattern:** OODA loop
- **Stages:** observe → orient → decide → act → verify
- **Spec:** [JARVIS_REASONING_PROTOCOL.md](../contracts/JARVIS_REASONING_PROTOCOL.md)
- **Implementation:** [src/jarvis_reasoning_protocol.py](../../src/jarvis_reasoning_protocol.py)

### Deliberation Runtime (`cognitive.deliberation`) — decision lobe (v1.2)

- **Stages:** options → tradeoffs → commit → revisit
- **Output:** `decision_object` with `criteria_scores`, `winning_criteria`, `commit_source`: `llm` | `deterministic`
- **Implementation:** [src/cog_runtime/deliberation.py](../../src/cog_runtime/deliberation.py), [deliberation_llm.py](../../src/cog_runtime/deliberation_llm.py)

### Attention Runtime (`cognitive.attention`) — focus lobe (v1.2)

- **Stages:** capture → filter → prioritize → hold
- **Output:** `focus_artifact` with `primary_focus`, `secondary_focus`, `focus_signals`, `weights`, `salience`, `signal_sources`
- **Implementation:** [src/cog_runtime/attention.py](../../src/cog_runtime/attention.py)

### Memory Runtime (`cognitive.memory`) — hippocampus runtime (v1.2)

- **Stages:** encode → index → retrieve → forget
- **Output:** episodic/semantic split plus `compressed_episodic`, `semantic_abstractions`
- **Implementation:** [src/cog_runtime/memory.py](../../src/cog_runtime/memory.py)

### Reflection Runtime (`cognitive.reflection`) — cross-lobe loop (v1.3)

- **Stages:** expect → compare → learn → adjust
- **Output:** `reflection_artifact` with `expected_outcome`, `alignment`, `gaps`, `adjustments`, `next_turn_hints`, `planning_handoff`
- **Implementation:** [src/cog_runtime/reflection.py](../../src/cog_runtime/reflection.py)

### Planning Runtime (`cognitive.planning`) — sequencing lobe (v1.3)

- **Stages:** orient → sequence → checkpoint → handoff
- **Output:** adaptive `chain_scores`, `chain_selection_reason`, plus `step_chains`, `active_chain_id`, `active_chain`, `chain_step_index`, `arc_step`, `steps`, `checkpoints`, `handoff_summary`, `next_action`, `execution_handoff`
- **Implementation:** [src/cog_runtime/planning.py](../../src/cog_runtime/planning.py)

### Execution Runtime (`cognitive.execution`) — action verification lobe (v1.2)

- **Stages:** bind → execute → verify → recover → rollback → report
- **Output:** tiered `recovery_paths`, `recovery_tier`, `rollback_policy`, `rollback_safe`, plus `bound_action`, `executed_steps`, `verification_status`, `recovery_action`, `recovered`, `rollback_target`, `rollback_applied`, `report`, `execution_complete`
- **Implementation:** [src/cog_runtime/execution.py](../../src/cog_runtime/execution.py)

### Cortex Arcs (v1.3)

- **Module:** [src/cog_runtime/arcs.py](../../src/cog_runtime/arcs.py)
- **Session key:** `session.metadata["cortex_arc"]`
- **Fields:** `arc_id`, `goal`, `goal_type`, `root_goal`, `subgoals`, `current_subgoal`, `goal_hierarchy` (with `goal_id`, `parent_id`, `status`), `closed_subgoals`, `goal_closure_status`, `status`, `turn_count`, `turns[]`, `open_threads[]`, `closed_threads[]`
- **Goal types:** `decision`, `continuity`, `exploration`, `repair`, `general`
- **Closure:** subgoals close on successful execution; parent root closes when all children complete

### Self-Tuning Invariants (v1.1)

- **Module:** [src/cog_runtime/tuning.py](../../src/cog_runtime/tuning.py)
- **Session key:** `session.metadata["cortex_invariant_tuning"]`
- **Tunable parameters:** `execution_overlap_min`, `focus_overlap_min`, `chain_advance_on_partial`
- **History:** bounded `tuning_history` (last 8 generations) with `drift_guarded` and `drift_score`

## Nova Cortex v3.0 (planned)

Persistent **multi-session cognitive identity** — not just per-session arcs. See [NOVA_CORTEX_V3_ROADMAP.md](./NOVA_CORTEX_V3_ROADMAP.md).

## wolf-cog-os-full Integration

See [NOVA_CORTEX_WOLF_INTEGRATION.md](./NOVA_CORTEX_WOLF_INTEGRATION.md) for boot stack, payload manifest, bridge, and verify gate.

OS operator summary: [wolf-cog-os/docs/NOVA_CORTEX_INTEGRATION.md](../../wolf-cog-os/docs/NOVA_CORTEX_INTEGRATION.md)

## Nova Integration Surface

| Function | Module | Role |
|----------|--------|------|
| `nova_cognitive_router()` | `src/cog_runtime/nova.py` | Selects active lobe IDs per turn |
| `nova_cognitive_session()` | `src/cog_runtime/nova.py` | Shared session + ledger |
| `nova_speaking_adapter()` | `src/cog_runtime/nova.py` | Wraps Speaking with deliberation artifacts |
| `nova_cortex_spec()` | `src/cog_runtime/` | Machine-readable cortex manifest |

## wolf-cog-os-full Binding

Edition: `wolf-cog-os-full`

- Payload manifest: `/opt/cogos/config/cognitive_runtime_family.json` (Nova Cortex v1 JSON)
- Bridge: [src/cogos_runtime_bridge.py](../../src/cogos_runtime_bridge.py)
- Governance registry loader: `runtime.cognitive_runtime_family`

## Verification

```bash
pytest tests/test_attention_runtime.py tests/test_deliberation_runtime.py tests/test_deliberation_llm.py tests/test_memory_runtime.py tests/test_reflection_runtime.py tests/test_planning_runtime.py tests/test_execution_runtime.py tests/test_tuning.py tests/test_cortex_arcs.py tests/test_integration_cog_runtimes.py tests/test_nova_face_bridge.py -q

python -c "from src.cog_runtime import nova_cortex_spec; print(nova_cortex_spec()['family_id'], nova_cortex_spec()['version'])"

python .github/scripts/check-nova-cortex-governance.py

python -m src.cogos_runtime_bridge --validate-config wolf-cog-os/payload/opt/cogos/config/cognitive_runtime_family.json
```

## Claim Status

Nova Cortex contract: **canonical** in this document.

Runtime behavior: **asserted** until cross-machine wolf-cog-os-full boot proof is filed.

See [FAMILY_V3_0_PROOF_BUNDLE.md](../proof/cognitive_runtime/FAMILY_V3_0_PROOF_BUNDLE.md). Next operator continuity evidence: [NARRATIVE_CONTINUITY_EVIDENCE_PLAN.md](../proof/cognitive_runtime/NARRATIVE_CONTINUITY_EVIDENCE_PLAN.md).
