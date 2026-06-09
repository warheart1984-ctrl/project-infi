# Authority Mask Spec Contract

Status: **active contract** (compilable lowering pipeline)

## Purpose

Lower Governance IR into provider-agnostic mask constraints at labeled decode/generation sites. Provider adapters consume this spec at runtime (Phase 7).

Schema id: `nova.authority_mask_spec.v1`

Module: `src/authority_mask_lowering.py`

Taxonomy: `docs/contracts/GOVERNANCE_TAXONOMY.md`

## Maskable sites

| Site ID | Position hint | Governed by |
|---------|---------------|-------------|
| `tool_call_schema` | Structured tool/function call emission | allowed verbs + action types + resources |
| `external_mutation_command` | Shell/file/network/provider mutations | execute-class verbs + OTEM boundary |
| `subagent_spawn_descriptor` | Child agent spawn payloads | `max_subagent_depth`, POLA delegation |
| `cisiv_stage_transition` | Stage advance / lifecycle mutations | stage-linked invariants + CISIV sequence |

Each site emits a `MaskableSite` record: `{site_id, position_hint, constraint_schema_ref}`.

## Lowering rules (IR → MaskConstraint)

| IR field | Mask output |
|----------|-------------|
| `authority_envelope.allowed_verbs` | `allowed_verbs` per site; forbidden = taxonomy minus allowed |
| `authority_envelope.resources` | `allowed_resource_classes` for mutation/spawn sites |
| `authority_envelope.delegation_depth` / `max_subagent_depth` | `max_child_scope` on `subagent_spawn_descriptor`; denied when depth cap reached |
| `execution_context.otem_level` + `otem_boundary` | `max_action_class` (observe/propose/execute) per site |
| `execution_context.cisiv_stage` | `allowed_action_classes` via taxonomy stage table |
| `invariant_set.hard` + `stage_linked` | Additional `deny_patterns` |

## Runtime hook

```python
def get_authority_mask(
    ir: dict[str, Any] | GovernanceIR,
    decode_context: dict[str, Any],
) -> MaskSpec:
    """Provider-agnostic mask from IR + decode position."""
```

`decode_context` keys (all optional):

- `site_id` — active maskable site
- `checkpoint_id` — CheckGraph node if mid-decode
- `provider_id` — capability matrix lookup (stub returns generic)
- `token_position` / `structured_field` — future logit/field masks

## MaskSpec schema

```json
{
  "mask_id": "sha256-16",
  "schema_id": "nova.authority_mask_spec.v1",
  "status": "compilable_target",
  "ir_fingerprint": "sha256-16",
  "taxonomy_fingerprint": "sha256-16",
  "sites": {
    "tool_call_schema": {
      "allowed_verbs": ["observe"],
      "forbidden_verbs": ["execute"],
      "allowed_resource_classes": ["session"],
      "max_action_class": "observe",
      "allowed_action_classes": ["observe"],
      "deny_patterns": ["unsigned_tool_call"],
      "denied": false
    }
  },
  "maskable_sites": [],
  "provider_hints": {
    "implementation": "adapter",
    "supported_surfaces": ["structured_output", "logit_mask", "sampling_config"]
  }
}
```

## ProviderMask (adapter output)

Adapters translate `authority_mask_spec` into a runtime `ProviderMask` (see `GOVERNANCE_PROVIDER_ADAPTERS.md`):

| Field | Source |
|-------|--------|
| `mask_surface` | `reference_mock` → `logit_mask`; `local` → `structured_output` + `sampling_config` |
| `generation_overrides` | Site `deny_patterns`, temperature caps, `max_tokens`, `stop` |
| `schema_constraints` | `tool_call_schema` / `external_mutation_command` allowed verbs & resources |
| `denied_token_ids` | Mock-only deterministic hashes from `forbidden_verbs` |
| `instruction_fragments` | Local adapter system-prompt authority clauses |

Registry: `get_governance_adapter(provider_id)` in `src/providers/governance_adapters.py`.

## Provider integration

| `provider_id` | Surface | Phase 7 behavior |
|---------------|---------|------------------|
| `reference_mock` | `logit_mask` | Deterministic denied token simulation; used in unit tests and eval harness |
| `local` | `structured_output`, `sampling_config` | Schema + sampling merge; post-decode `validate_decoded_output` |
| `openai_compatible`, `anthropic`, `openrouter`, … | passthrough | `implementation: "stub"` — no mask enforcement yet |

Future vendor-specific surfaces may add `mask_logits(logits, mask_spec, step)` without changing the compiler spec.

Nova organ (`invariant_engine_organ`) remains read-only — no mask authority.

## Related contracts

- `GOVERNANCE_IR.md` — compiler input
- `GOVERNANCE_TAXONOMY.md` — shared vocabulary
- `INVARIANT_DECODE_GOVERNANCE.md` — bundle consumer
- `GOVERNANCE_PROVIDER_ADAPTERS.md` — adapter protocol and registry
