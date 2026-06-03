# URG Mission Contract (URG-MC-01)

Status: **v1.2** — AAIS step bridge, auto-assign, HMAC receipt

Authority: `docs/contracts/URG_STACK_DOCTRINE.md`, `docs/contracts/URG_CLOUD_INVARIANTS.md`.

## Definition

URG’s atomic unit is the **Governed Composite Mission** (GCM):

\[
M = (G, C, O, I, L)
\]

| Symbol | Field | Payload |
|--------|-------|---------|
| \(G\) | Goal | `governed_composite_mission.goal` — intent, objective, operator, tenant, region |
| \(C\) | Constraints | `governed_composite_mission.constraints` — cost, risk, region, halt policy |
| \(O\) | Participating organs | `governed_composite_mission.participating_organs` — admitted \(O_i\) with contracts |
| \(I\) | Invariant set | `governed_composite_mission.invariant_set` — six cloud families + per-step results |
| \(L\) | Ledger trail | `governed_composite_mission.ledger_trail` — `missions.jsonl` forensic chain |

Phases (also in `urg_phases`): `decompose` → `assign` → `enforce` → `receipt`.

The **signed mission receipt** (`mission_receipt`) is a SHA-256 signature over goal, constraints, organs, invariant verdict, ledger action ids, and ingress stamp. If there is no receipt, the mission did not complete URG law.

AAIS continues to own per-turn bridge clearance inside each step’s governed proposal envelope.

## Request — `POST /api/ugr/mission/run`

```json
{
  "operator_id": "operator-demo",
  "tenant_id": "tenant:acme",
  "aais_instance_id": "aais-local-1",
  "region_id": "tenant-us",
  "intent": "governed_super_router_demo",
  "objective": "Prove one mission across three provider organs under cost and region law.",
  "constraints": {
    "max_total_cost_units": 25,
    "risk_ceiling": "medium",
    "required_region": "tenant-us"
  },
  "steps": [
    {
      "step_id": "scout",
      "objective": "Bounded local scout pass",
      "organ_id": "organ-local-tiny"
    },
    {
      "step_id": "relay",
      "objective": "Mid-tier relay pass",
      "organ_id": "organ-openrouter-mid"
    },
    {
      "step_id": "synth",
      "objective": "High-tier synthesis pass",
      "organ_id": "organ-openai-big"
    }
  ],
  "halt_on_failure": true,
  "aais_step_bridge": true,
  "step_deliberation_mode": "llm_bridge"
}
```

### Flags (v1.2)

| Field | Default | Values |
|-------|---------|--------|
| `aais_step_bridge` | `true` | `false` = routing-only (static proposals) |
| `step_deliberation_mode` | `llm_bridge` | `full_deliberate` = full UGR deliberation per step |
| `steps[].organ_id` | optional | Omit and use `steps[].tier` or ordinal heuristic for auto-assign |

## Response

```json
{
  "mission_id": "mission-…",
  "status": "ok | blocked | rejected",
  "governed_composite_mission": {},
  "mission_receipt": { "receipt_signature": "…", "ingress_stamp_hash": "…" },
  "urg_phases": { "decompose": {}, "assign": {}, "enforce": {}, "receipt": {} },
  "urg_ingress": {},
  "steps": [],
  "ledger_refs": [],
  "summary": "string"
}
```

Each step entry includes:

- `action_id`, `organ_id`, `provider`, `cost_units`
- `invariant_results[]`
- `proposal` (governed envelope, proposal-only)
- `prior_action_id` (causality chain)

## Provider organs config

`deploy/ugr/provider-organs.json` — three demo organs minimum.

## Non-negotiables

1. Mission must carry `urg_ingress.stamp` from `UrgIngressLaw`.
2. Every step routes only through declared `organ_id`.
3. Provider execution is gated by `execution_mode` (see below) and `URG_MISSION_KILL_SWITCH`.
4. All accepted actions append to `collective-pattern-ledger/unified/missions.jsonl` (runtime dir mirror).

## Execution lifecycle (v1.5+)

| State | Meaning |
|-------|---------|
| `execution_planned` | Steps and organs assigned; no provider I/O |
| `execution_dispatched` | Provider call issued; awaiting response |
| `execution_committed` | Provider ack + ledger phase rows + `B_cloud(M)` still satisfied — irreversible causal chain |
| `execution_simulated` | `DRY_RUN` only — full plan/receipt path, no provider calls |

**`execution_committed`** requires: provider execution status `EXECUTED`, ledger writes (`mission_ingress`, `organ_assignment`, `provider_dispatch`, `provider_ack`), and `cloud_execution_safety` pass at the execution organ boundary.

## Execution modes

| Mode | Provider calls | Downstream | Receipt `shadow` |
|------|----------------|------------|------------------|
| `DRY_RUN` (default) | No (simulated) | N/A | false |
| `SHADOW_EXECUTION` | Yes | Results discarded | true |
| `LIVE_EXECUTION` | Yes | Results may flow | false |

Env: `URG_EXECUTION_MODE` (mission field overrides). Legacy: `UGR_LLM_EXECUTE=1` → `LIVE_EXECUTION`.

**Kill switch:** `URG_MISSION_KILL_SWITCH=1` rejects new missions; in-flight may set `operator_abort` to halt.

First no-risk live mission: `deploy/ugr/mission-demo-healthcheck-embedding.json` (`healthcheck-embedding`, tier tiny, rail `SAFE`, region `tenant-us`).

## Multi-tenant isolation (v1.6)

- `TenantRegistry` + `tenant_manifold` gate every mission at open
- Ledger: `{runtime}/collective-pattern-ledger/tenants/{tenant-slug}/missions.jsonl`
- Receipts: `{runtime}/urg/receipts/{tenant-slug}/receipts.jsonl`
- `GET /api/ugr/mission/receipt/<id>?tenant_id=` required (unless `URG_RECEIPT_ADMIN=1`)
- Tenant organ overlay: `deploy/ugr/tenants/{tenant-slug}/provider-organs.json`
- Federation: `federation_target_tenant` + `federation_grant_id` must match tenant `federation_grants[]` (static + accepted runtime grants in `urg/federation/grants.jsonl`)

## Federation v1.7–v1.9

**Bilateral grants:** `POST /api/ugr/federation/issue` (pending) → grantee `POST /api/ugr/federation/accept` (accepted + inbound audit row).

**Federated step** (home tenant owns mission):

```json
{
  "step_id": "peer-relay",
  "organ_id": "organ-local-tiny",
  "federation_peer_tenant": "tenant:contoso",
  "federation_grant_id": "fed-..."
}
```

Ledger phases: home `federation_step`; peer `federation_inbound` (includes `home_mission_id`, `grant_id`).

**Receipt v1.3:** `federation_digest`, `counterparty_receipt_ref` (peer stub under grantee receipts).

**Governance:** `mutation_op` = `federation_organ_admit` | `federation_organ_suspend` requires grant capability `governance_cosign` and dual ledger rows when `URG_GOVERNANCE_APPLY=1`.

## Cost routing (v1.6)

- `constraints.mission_budget`: `{soft_ceil, hard_ceil, per_step_max}`
- Organ `contract.cost_contract`: `{cost_per_call, cost_per_token, region_multiplier}`
- `failure_reason: BUDGET_EXCEEDED` on hard ceiling breach

## Governed marketplace (v1.6)

- `GET /api/ugr/marketplace/organs?tenant_id=`
- Governance ops: `mutation_op` = `organ_admit` | `organ_suspend` | `organ_evict` (apply via `URG_GOVERNANCE_APPLY=1`)
- `trust_score` gates LIVE vs SHADOW execution per organ

## Verification

```bash
make ugr-mission-gate
py -3.12 tools/proof/run_ugr_mission_demo.py
```
