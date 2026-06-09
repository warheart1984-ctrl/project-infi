# Governance Provider Adapters Contract

Status: **active contract** (Phase 7)

## Purpose

Consume compiler outputs (`authority_mask_spec`, `decode_governance_bundle`) at the provider boundary without importing provider SDKs into the pure compiler layer.

Module: `src/providers/governance_adapters.py`

Registry: `get_governance_adapter(provider_id)`

## Invariants

1. `invariant_compiler.py` remains pure — no provider imports, no runtime side effects.
2. Adapters read compiled specs only; they do not re-derive IR lowering.
3. Stub adapters (`openai_compatible`, `anthropic`, `openrouter`, …) passthrough masks and return `ALLOW` with `implementation: "stub"` metadata.
4. Reference adapters (`reference_mock`, `local`) are deterministic and testable without GPU/network.

## Protocol

```python
class GovernanceProviderAdapter(Protocol):
    def apply_authority_mask(
        self, provider_ctx: ProviderContext, authority_mask_spec: dict[str, Any]
    ) -> ProviderMask: ...

    def run_decode_governance(
        self, provider_ctx: ProviderContext, decode_governance_bundle: dict[str, Any]
    ) -> DecodeGovernanceDecision: ...
```

Module-level helpers:

- `apply_authority_mask(provider_ctx, authority_mask_spec)` — resolves adapter via `provider_ctx.provider_id`
- `run_decode_governance(provider_ctx, decode_governance_bundle)` — same resolution

## Shared types

### ProviderContext

| Field | Role |
|-------|------|
| `provider_id` | Registry key |
| `site_id` | Active maskable site (default `tool_call_schema`) |
| `decode_context` | Optional checkpoint/token hints |
| `provider_request` | Outbound generation request dict |
| `messages` | Chat messages when applicable |
| `checkpoint_failures` | Post-checkpoint hard_fail nodes |
| `attempt` | Rollback loop attempt index |
| `decoded_output` | Structured output for post-decode validation |

### ProviderMask

| Field | Role |
|-------|------|
| `mask_surface` | `logit_mask` \| `structured_output` \| `sampling_config` |
| `generation_overrides` | `temperature`, `max_tokens`, `stop`, etc. |
| `schema_constraints` | JSON-schema / tool schema fragments |
| `denied_token_ids` | Synthetic ids (mock surface only) |
| `instruction_fragments` | System-prompt authority clauses |
| `metadata` | `implementation`, `provider_id`, trace fields |

### DecodeGovernanceDecision

| Field | Role |
|-------|------|
| `decision` | `ALLOW` \| `RETRY` \| `ROLLBACK` \| `ESCALATE` \| `BLOCK` |
| `sampling_tighten` | Apply temperature cap tightening on violation |
| `retry_hint` | Human/agent-readable retry guidance |
| `rollback_action` | Named action from `rollback_policy.actions` |
| `generation_overrides` | Per-attempt sampling adjustments |
| `details` | Adapter-specific diagnostics |

## Registered adapters

| `provider_id` | Class | Behavior |
|---------------|-------|----------|
| `reference_mock` | `ReferenceMockAdapter` | Deterministic `logit_mask`; maps forbidden verbs to hashed `denied_token_ids`; rollback/retry from bundle policy |
| `local` | `LocalGovernanceAdapter` | `structured_output` + `sampling_config`; merges schema constraints and instruction fragments; `validate_decoded_output` for verb violations |
| `openai_compatible`, `anthropic`, `openrouter`, `claude`, `http_chat` | `StubGovernanceAdapter` | Passthrough mask; `ALLOW` decision; `implementation: "stub"` |

## Runtime wiring

| Consumer | Hook |
|----------|------|
| `src/ugr/governed_llm_executor.py` | Before `adapter.invoke()`: `apply_authority_mask` → merge into `provider_request` / messages; attach `provider_mask` to response |
| `src/decode_governance_executor.py` | After post-checkpoint `hard_fail`: `run_decode_governance` → apply `sampling_tighten` / `generation_overrides`; record `adapter:{decision}` in rollback trace |

Backward compatibility: when `decode_governance_bundle` lacks `authority_mask_spec`, executors fall back to pre-Phase-7 behavior.

## Helper utilities

- `merge_mask_into_provider_request(request, mask)` — shallow merge of overrides and metadata
- `merge_mask_into_messages(messages, mask)` — append `instruction_fragments` to system role
- `validate_decoded_output(output, mask, site_id)` — local post-decode verb check
- `adapter_registry_snapshot()` — introspection for tests/docs

## Stub guarantees

Stub adapters never block execution. They exist so multi-provider routing can be exercised before vendor-specific mask surfaces are implemented. Production integrations should replace stubs with surface-specific adapters while preserving the protocol types.

## Related contracts

- `AUTHORITY_MASK_SPEC.md` — compiler mask output
- `INVARIANT_DECODE_GOVERNANCE.md` — bundle shape consumed by `run_decode_governance`
- `GOVERNED_TRAINING_PIPELINES.md` — eval harness optional runtime replay via `reference_mock`

## Tests

- `tests/test_governance_provider_adapters.py`
- `tests/test_governed_llm_executor_adapters.py`
- `tests/test_decode_governance_executor.py` (adapter-driven retry/rollback)
