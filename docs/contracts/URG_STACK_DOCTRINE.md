# URG Stack Doctrine

Status: **active contract** (mission-level governance v1)

Authority: `META_ARCHITECT_LAWBOOK.md`, `docs/contracts/UGR_RUNTIME_CONTRACT.md`, `docs/contracts/AAIS_COGNITIVE_BRIDGE_RUNTIME_LAW.md`.

## Naming (non-negotiable)

| Name | Role | Is it a model? |
|------|------|----------------|
| **AAIS** | Governed cognitive runtime — per-turn invariants, bridge, lanes, operator shell | No |
| **URG** | Unified Runtime Governance — lawbook + switchboard for many AAIS instances and LLM providers | **No** |

URG is not “another model.” It does not generate answers. It governs **which** governed runtime may act, **which** provider organ may be invoked, and **whether** the action may be ledgered.

## Atomic unit of governance

| Layer | Atomic unit | Owner |
|-------|-------------|-------|
| AAIS | **Turn** — one operator message through bridge + lanes | `src/api.py`, Cognitive Bridge |
| URG | **Governed Composite Mission** \(M\) | `src/ugr/mission/` |

\[
M = (\text{Goal}, \text{Constraints}, \text{Participating Organs}, \text{Invariant Set}, \text{Ledger Trail})
\]

URG executes four phases on every admitted mission:

1. **Decompose** — sub-goals from `steps[]`
2. **Assign** — bind organs (AAIS instances + external providers) under \(K_i\)
3. **Enforce** — cross-organ cloud invariants per step
4. **Receipt** — signed `mission_receipt` over forensic ledger + verdict

Per-request routing is a step inside \(M\). Per-session continuity stays AAIS. URG’s power is the composite: budgets, regions, provider sets, and causal chains are mission-global; the receipt is the proof bundle.

## Provider organs (not gods)

Each external LLM or tool is a **provider organ**:

\[
O_i = (I_i, E_i, F_i, K_i)
\]

| Symbol | Meaning | Repo surface |
|--------|---------|--------------|
| \(I_i\) | Identity — organ id, tier, class | `provider-organs.json` → `identity` |
| \(E_i\) | Envelope — execution backend, proposal-only | `envelope` |
| \(F_i\) | Function — capabilities, token bounds | `function` |
| \(K_i\) | Governance contract — cost, risk, regions, domains | `contract` |

URG routes across organs under invariants. No organ is trusted; only admitted contracts are.

## Cloud invariant lift

AAIS turn invariants (Identity, Boundary, Continuity, Causality, Mutation, Composite) have **cloud analogs** enforced at mission scope. See `docs/contracts/URG_CLOUD_INVARIANTS.md`.

URG is **Composite Invariant for the super-cloud**: the only layer that may compose cross-provider, cross-region, cross-instance outcomes into one admissible mission result.

## Ingress law

**If it did not pass through URG, it does not exist.**

- No AAIS instance LLM call, tool execution, or ledger write for cloud-scale work may bypass `src/ugr/mission/ingress.py`.
- Deliberation (`POST /api/ugr/deliberate`) remains bridge-first; **missions** (`POST /api/ugr/mission/run`) are the narrow super-router demo surface.
- Direct provider registry invocation from product code without a mission `action_id` is out of law for governed cloud paths.

## First demo (v1)

One mission, three provider organs, cost + risk + region constraints, fully ledgered.

```bash
make ugr-mission-gate
py -3.12 -m pytest tests/test_ugr_mission_demo.py -q
py -3.12 tools/proof/run_ugr_mission_demo.py
```

Contract: `docs/contracts/URG_MISSION_CONTRACT.md`.
