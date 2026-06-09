# Invariant Decode Governance v1 — Proof

Status: **v1 slice complete**

## Claim

Governance law is compiled from a single **Governance IR** snapshot into a **DecodeGovernanceBundle**, and the UGR LLM lane executes with checkpoint traversal, rollback, and escalation — without duplicating invariant math.

## Evidence

### Layer 1 — Governance IR

| Artifact | Path |
|----------|------|
| Contract | `docs/contracts/GOVERNANCE_IR.md` |
| Builder | `src/governance_ir.py` → `build_governance_ir` |
| Tests | `tests/test_governance_ir.py` |

Properties demonstrated:

- Deterministic `ir_fingerprint` from canonical JSON.
- Authority envelope, invariant set classification, execution context projection.

### Layer 2 — Compiler + Approach 2 runtime

| Artifact | Path |
|----------|------|
| Contract | `docs/contracts/INVARIANT_DECODE_GOVERNANCE.md` |
| Compiler | `src/invariant_compiler.py` → `compile_from_ir`, `apply_ingress_plan`, `run_admission_checks` |
| Executor | `src/decode_governance_executor.py` → `execute_with_decode_governance` |
| Tests | `tests/test_invariant_compiler.py`, `tests/test_decode_governance_executor.py` |

Runtime loop (UGR lane via `src/ugr/llm_lane.py`):

1. Ingress plan (delegates to `InvariantEngine.validate_bridge_packet`).
2. Pre-execution checkpoint validators.
3. Generate candidate → post-checkpoint → rollback on violation → re-sample.
4. On exhaustion → OTEM gate or BLOCK.

### Layer 4 baseline — IR-fed packet path

| Surface | Change |
|---------|--------|
| `cognitive_bridge.route_to_bridge` | Ingress via `apply_ingress_plan` from compiled bundle |
| `cognitive_bridge._finalize_bridge_result` | Attaches `governance_ir` + `decode_governance_bundle` |
| `chat_turn_governance.finalize_chat_turn_admission` | Admission via `run_admission_checks` when bundle present |

Parity: `test_apply_ingress_plan_matches_bridge_invariant` asserts ingress allows same as direct `validate_bridge_packet`.

### Layer 3 + Layer 4 training (design, v1)

- `AuthorityMaskSpec` and `TrainingViewSpec` emitted with `status: design_target` in v1.
- Provider capability matrix documented in `INVARIANT_DECODE_GOVERNANCE.md`.
- No logit masking or training pipeline in v1.

### v2 compilable slice — mask + training view specs

| Artifact | Path |
|----------|------|
| Shared taxonomy contract | `docs/contracts/GOVERNANCE_TAXONOMY.md` |
| Shared taxonomy module | `src/governance_taxonomy.py` |
| Authority mask contract | `docs/contracts/AUTHORITY_MASK_SPEC.md` |
| Authority mask lowering | `src/authority_mask_lowering.py` → `lower_authority_mask`, `get_authority_mask` |
| Training view contract | `docs/contracts/TRAINING_VIEW_SPEC.md` |
| Training view projection | `src/training_view_spec.py` → `project_training_view`, `build_training_view_spec` |
| Compiler wiring | `src/invariant_compiler.py` emits `taxonomy_ref`, `compilable_target` specs |
| Mask tests | `tests/test_authority_mask_lowering.py` |
| Training tests | `tests/test_training_view_spec.py` |

Properties demonstrated:

- Both specs share `ir_fingerprint` and `taxonomy_fingerprint` with the source IR.
- Mask lowering is deterministic and site-scoped (`tool_call_schema`, `external_mutation_command`, `subagent_spawn_descriptor`, `cisiv_stage_transition`).
- Training projection stubs produce `COMPLIANT` / `VIOLATION` labels aligned with mask constraints.
- Provider logit masking and actual training runs remain out of scope for v2 compiler slice.

### Phase 7 — provider adapter consumption

| Artifact | Path |
|----------|------|
| Adapter contract | `docs/contracts/GOVERNANCE_PROVIDER_ADAPTERS.md` |
| Adapter module | `src/providers/governance_adapters.py` |
| Runtime: mask merge | `src/ugr/governed_llm_executor.py` |
| Runtime: decode decisions | `src/decode_governance_executor.py` |
| Tests | `tests/test_governance_provider_adapters.py`, `tests/test_governed_llm_executor_adapters.py` |

Properties demonstrated:

- `reference_mock` applies deterministic `logit_mask` simulation from `authority_mask_spec`.
- `local` merges `structured_output` / `sampling_config` into provider requests.
- Stub providers passthrough with `ALLOW`; backward compatible when bundle lacks `authority_mask_spec`.
- `invariant_compiler.py` unchanged — adapters import only from runtime/executor layers.

### Phase 8 — governed training + eval

| Artifact | Path |
|----------|------|
| Training pipelines (design) | `docs/contracts/GOVERNED_TRAINING_PIPELINES.md` |
| Batch API | `src/training_view_spec.py` → `build_training_examples` |
| Eval harness | `src/governance_eval_harness.py` |
| Tests | `tests/test_training_examples.py`, `tests/test_governance_eval_harness.py` |

Properties demonstrated:

- Multi-source batch generation with `view_id` dedup and stable ordering.
- Label parity via `infer_label_from_mask` on embedded IR snapshots.
- Optional runtime replay through `execute_with_decode_governance` + `reference_mock`.

## Verification commands

```powershell
.venv\Scripts\python.exe -m pytest tests/test_governance_provider_adapters.py tests/test_governed_llm_executor_adapters.py tests/test_decode_governance_executor.py tests/test_training_examples.py tests/test_governance_eval_harness.py tests/test_authority_mask_lowering.py tests/test_training_view_spec.py tests/test_invariant_compiler.py -q
```

Legacy slice:

```powershell
.venv\Scripts\python.exe -m pytest tests/test_governance_ir.py tests/test_invariant_compiler.py tests/test_decode_governance_executor.py tests/test_authority_mask_lowering.py tests/test_training_view_spec.py -q
```

## Boundaries preserved

- Compiler calls `InvariantEngine`; does not reimplement domain invariants.
- Governed LLM remains proposal-only; Approach 2 runs after PROPOSED envelope.
- Nova organ read-only; no execution authority from attestation organ.
- Provider adapters live outside `invariant_compiler.py`.

## Limitations (remaining)

- No draft-model speculative decoding; full generation + rollback only.
- Vendor HTTP adapters remain stubs; no live logit masking on OpenAI/Anthropic APIs.
- No fine-tuning, reward model training, or RLAIF trainers wired (`train_jarvis_lora.py` not connected).
- `plan_branch` rollback disabled; draft buffer / ODL rollback marked not persisted.
