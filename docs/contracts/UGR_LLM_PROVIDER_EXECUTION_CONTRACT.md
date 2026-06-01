# UGR Governed LLM Provider Execution Contract

Authority: `docs/contracts/AAIS_COGNITIVE_BRIDGE_RUNTIME_LAW.md`

## Scope

Adds a **governed execution commit layer** after the proposal-only governed LLM seam:

- `src/ugr/governed_llm_executor.py` — maps `PROPOSED` envelopes to provider adapters
- UGR LLM lane attaches `governed_llm_execution` when enabled
- Proposal envelope remains unchanged (`proposal_only: true`, `execution_authority: none`)

Execution is a separate commit with `execution_authority: governed_commit`.

## Enablement

| Variable | Value | Effect |
|---|---|---|
| `UGR_LLM_EXECUTE` | `1` | Allow provider invoke after PROPOSED envelope + bridge ALLOW/DEGRADE |

Default: execution **disabled** (proposal-only lane preserved).

## Invariants

1. Invalid or BLOCKED envelopes never invoke providers
2. Temperature cap 0.0 from UGR LLM lane applies to execution
3. Provider must pass `provider_registry.can_invoke`
4. Envelope validation (`validate_governed_llm_envelope`) required before execution

## Verification

```bash
make ugr-llm-provider-gate
```

Evidence: `docs/proof/ugr/UGR_LLM_PROVIDER_EXECUTION_PROOF.md`
