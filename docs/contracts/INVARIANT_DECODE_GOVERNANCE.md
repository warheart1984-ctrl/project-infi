# Invariant Decode Governance Contract

Status: **active contract**

## Purpose

The invariant compiler lowers **Governance IR** into runtime artifacts consumed by decode-time governance (Approach 2) and documented endgame paths (Approach 1 masks, Approach 3 training views). This contract defines those artifacts and their lowering rules.

Pipeline:

```
Law sources → Governance IR → compile_from_ir → DecodeGovernanceBundle → runtime
```

## DecodeGovernanceBundle (v1)

```json
{
  "compiler_version": "aais.invariant_compiler.v1",
  "ir_version": "aais.governance_ir.v1",
  "ir_fingerprint": "sha256-16",
  "bundle_fingerprint": "sha256-16",
  "check_graph": { "ir_fingerprint": "...", "nodes": [] },
  "rollback_policy": { "max_rollbacks": 2, "tighten_on_violation": true, "actions": [] },
  "escalation_hooks": {
    "max_attempts": 4,
    "escalate_to": "block|otem|operator",
    "otem_gate": false,
    "operator_approval": false
  },
  "ingress_plan": { "validators": ["bridge_invariant"], "fail_closed": true },
  "taxonomy_ref": "nova.governance_taxonomy.v1",
  "authority_mask_spec": { "status": "compilable_target", "schema_id": "nova.authority_mask_spec.v1", "...": "..." },
  "training_view_spec": { "status": "compilable_target", "schema_id": "nova.training_view_spec.v1", "...": "..." }
}
```

Compiler entry: `src/invariant_compiler.py` → `compile_from_ir(ir)`.

Compiler errors raise `InvariantCompilerError` and must fail-closed (BLOCK) at bridge ingress.

---

## CheckGraph

Ordered invariant traversal nodes. Each node:

| Field | Type | Description |
|-------|------|-------------|
| `position` | string | `ingress`, `checkpoint`, `admission`, `subagent_spawn`, `external_mutation` |
| `validator` | string | Validator id (delegates to existing surfaces) |
| `required` | bool | Default `true` |

### v1 validators

| Position | Validator | Delegates to |
|----------|-----------|--------------|
| ingress | `bridge_invariant` | `InvariantEngine.validate_bridge_packet` |
| checkpoint | `bridge_invariant` | same |
| checkpoint | `governed_llm_envelope` | `validate_governed_llm_envelope` |
| checkpoint | `proposal_only` | envelope `proposal_only == true` |
| checkpoint | `temperature_zero` | UGR temperature cap (`UGR_LLM_TEMPERATURE`) |
| admission | `bridge_invariant` | same |
| admission | `chat_turn_contract` | chat turn law surface (v1 stub pass) |
| external_mutation | `effectful_execution_is_governed` | when `effectful_execution` capability present |
| subagent_spawn | `delegation_depth_within_cap` | when `delegation_depth < max_subagent_depth` |

Runtime: `decode_governance_executor.run_checkpoint_validators` traverses checkpoint nodes.

---

## RollbackPolicy

| Field | Description |
|-------|-------------|
| `max_rollbacks` | Re-sample attempts after checkpoint violation (default 2; 1 when many hard invariants) |
| `tighten_on_violation` | Re-apply UGR temperature cap between attempts |
| `actions` | Rollback targets on violation |

### v1 rollback actions

| Target | v1 behavior |
|--------|-------------|
| `draft_buffer` | Marked for discard (no persistent draft store yet) |
| `proposed_odl_node` | Marked for discard |
| `conversation_memory_assistant_turn` | `conversation_memory.get_session(id).rollback_last_assistant_turn()` |
| `plan_branch` | Disabled in v1 |

Runtime: `decode_governance_executor.execute_with_decode_governance` rollback loop.

---

## EscalationHooks

After rollback budget exhaustion:

| `escalate_to` | When | Action |
|---------------|------|--------|
| `block` | Default | Fail-closed BLOCK |
| `otem` | `otem_level` in `detected`, `blocked` | `maybe_enqueue_otem_execution_approval` |
| `operator` | `otem_level` == `approved` | Operator approval required (v1 returns ESCALATED) |

---

## IngressPlan

Thin wrapper over ingress-position CheckGraph nodes. Entry: `apply_ingress_plan(normalized, governance, decode_bundle=...)`.

- Delegates `bridge_invariant` to `InvariantEngine.validate_bridge_packet`.
- `fail_closed: true` — any ingress failure blocks bridge routing.

Wired in: `cognitive_bridge.route_to_bridge` for `BRIDGE_INVARIANT_PACKET_TYPES`.

---

## Admission (Layer 4 baseline)

Entry: `run_admission_checks(normalized, governance, decode_bundle=...)`.

Wired in: `chat_turn_governance.finalize_chat_turn_admission` (swallows errors for parity with prior behavior).

---

## Approach 1 — AuthorityMaskSpec (compilable target)

Status: **`compilable_target`** — IR lowering is implemented; provider logit masking remains out of scope.

Full contract: [`AUTHORITY_MASK_SPEC.md`](AUTHORITY_MASK_SPEC.md)

- Module: `src/authority_mask_lowering.py`
- Entry: `lower_authority_mask(ir, decode_context)` → `MaskSpec` dict
- Public hook: `get_authority_mask(ir, decode_context)` (provider-agnostic)
- Maskable sites: `tool_call_schema`, `external_mutation_command`, `subagent_spawn_descriptor`, `cisiv_stage_transition`
- Vocabulary: [`GOVERNANCE_TAXONOMY.md`](GOVERNANCE_TAXONOMY.md)

Provider adapters (`mask_logits`, `DecodeGovernanceHook`) are documented stubs only. Nova organ (`invariant_engine_organ`) remains read-only.

---

## Approach 3 — TrainingViewSpec (compilable target)

Status: **`compilable_target`** — projection stubs implemented; training runs remain out of scope.

Full contract: [`TRAINING_VIEW_SPEC.md`](TRAINING_VIEW_SPEC.md)

- Module: `src/training_view_spec.py`
- Entry: `project_training_view(ir, source=..., usage_mode=...)` → `TrainingViewRecord`
- Label inference: `infer_label_from_mask(ir, action_type, verb, resource_class)`
- Generation sources: `odl_trace`, `synthetic_compliant`, `synthetic_violation`, `fuzzed_envelope`
- Vocabulary: [`GOVERNANCE_TAXONOMY.md`](GOVERNANCE_TAXONOMY.md)

---

## Runtime consumers

| Consumer | Artifact | Module |
|----------|----------|--------|
| Bridge ingress | IngressPlan | `cognitive_bridge.route_to_bridge` |
| UGR LLM lane | CheckGraph + RollbackPolicy + EscalationHooks | `decode_governance_executor` |
| Chat admission | CheckGraph admission nodes | `chat_turn_governance` |
| UL audit | bundle fingerprints on bridge results | `aais_ul_substrate.wrap_bridge_result` |

## Fail-closed

- `InvariantCompilerError` / `GovernanceIRValidationError` at ingress → BLOCK.
- Checkpoint `hard_fail` → rollback or BLOCK.
- Escalation exhaustion → BLOCK or OTEM enqueue.

## Related contracts

- `GOVERNANCE_IR.md` — compiler input
- `GOVERNANCE_TAXONOMY.md` — shared vocabulary for mask and training lowering
- `AUTHORITY_MASK_SPEC.md` — Approach 1 compilable mask artifact
- `TRAINING_VIEW_SPEC.md` — Approach 3 compilable training view artifact
- `INVARIANT_ENGINE_RUNTIME.md` — InvariantEngine delegation
