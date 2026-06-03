# UGR Subsystem Discovery Contract (Proof-of-Subsystem v1.0)

Governed discovery of runtime subsystem specs under URG cloud law. A spec is **valid** when it passes organ graph, cloud invariant subset, rail schedulability, and tenant-class checks. Valid specs receive a canonical `subsystem_id = SHA256(normalized_spec)` and a signed `subsystem_discovery_receipt`.

## Spec space

| Field | Type | Notes |
|-------|------|-------|
| `role` | string | Maps to organ `capabilities` / `allowed_domains` (aliases: `llm_executor` → `general_qa`) |
| `io_shape` | object | `{ "inputs": [...], "outputs": [...] }` — at least one non-empty list |
| `rail_class` | enum | `SAFE` \| `NORMAL` \| `EXPRESS` |
| `risk_ceiling` | enum | `low` \| `medium` \| `high` |
| `tenant_class` | enum | `global` \| `standard` \| `restricted` — must match tenant manifold |

## Validity (fail-closed)

1. **Organ graph** — ≥1 admitted provider organ matches role, risk, rail.
2. **Cloud invariants** — `cloud_identity`, `cloud_boundary`, `cloud_forge_rail` on synthetic mission state.
3. **Rail compatibility** — Cloud Forge scheduled rail ≤ requested `rail_class`.
4. **Tenant class** — matches derived class for `tenant_id` (or constraint allow-list).

## API

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/ugr/discover/subsystem` | Hybrid validate or bounded search |
| GET | `/api/ugr/discover/subsystem/<subsystem_id>?tenant_id=` | Fetch receipt |
| GET | `/api/ugr/discover/subsystems?tenant_id=&since=&limit=` | Shadow catalog |

### POST body

```json
{
  "tenant_id": "tenant:acme",
  "operator_id": "op-1",
  "aais_instance_id": "aais-local",
  "spec": { "role": "llm_executor", "io_shape": {"inputs": ["text"], "outputs": ["text"]}, "rail_class": "NORMAL", "risk_ceiling": "low", "tenant_class": "standard" },
  "seed": {},
  "constraints": { "roles": ["llm_executor"], "rail_classes": ["NORMAL"] },
  "max_attempts": 64,
  "promote": false
}
```

### Response status

| status | Meaning |
|--------|---------|
| `discovered` | Valid spec; receipt emitted (idempotent if already known) |
| `invalid` | Spec present but failed validity |
| `not_found` | Search exhausted without valid spec |
| `rejected` | Kill switch or missing required fields |

## Receipt

Schema: `schemas/ugr_subsystem_discovery_receipt.v1.json`

Persistence:

- `{AAIS_RUNTIME_DIR}/urg/discovery/{tenant_slug}/discoveries.jsonl`
- `{AAIS_RUNTIME_DIR}/urg/discovery/{tenant_slug}/catalog.jsonl` (shadow catalog)

Signing: `URG_RECEIPT_SIGNING_KEY` (same as MissionReceipt).

## Environment

| Variable | Default | Purpose |
|----------|---------|---------|
| `UGR_SUBSYSTEM_DISCOVERY_ENABLED` | `1` | Kill switch |
| `UGR_DISCOVERY_SHADOW_ONLY` | `1` | Block promotion unless `0` |
| `URG_GOVERNANCE_APPLY` | off | Required for `promote: true` organ overlay writes |

## Promotion (optional)

`promote: true` with `URG_GOVERNANCE_APPLY=1` and `UGR_DISCOVERY_SHADOW_ONLY=0` runs a governance `organ_admit` mutation cloning the matched template organ into the tenant overlay.

## Lifecycle and operator rewards

Proof-of-Subsystem is the first half of the governed cognitive economy lifecycle:

`Discovery → Proof → Receipt → Governance → Promotion → Adoption → Attribution → Reward`

Discovery responses include `operator_rewards` when incentives are enabled (reputation-primary; credits are utility-only). See [UGR_OPERATOR_REWARDS_CONTRACT.md](UGR_OPERATOR_REWARDS_CONTRACT.md).

## Implementation

- `src/ugr/discovery/subsystem_spec.py`
- `src/ugr/discovery/subsystem_validity.py`
- `src/ugr/discovery/subsystem_discovery.py`
- `src/ugr/discovery/subsystem_discovery_receipt.py`
- `src/ugr/discovery/subsystem_discovery_store.py`
