# Cloud Forge Rail Scheduler Contract

Status: **active** (Phase 1 implementation in `src/cloud_forge/`).

Authority: `META_ARCHITECT_LAWBOOK.md`, `REPO_PROOF_LAW.md`, `docs/cloud-forge-governed-accelerator-program.md`.

Blueprint: `document/blueprints/PROJECT_BLUEPRINTS_MASTER.md` §1.6 Cloud Forge.

Failsafe: `docs/failsafe/cloud-forge-rail-failsafe.md`.

URG integration (tenant binding + federated peer rails): `src/ugr/cloud_forge_bridge.py`, [URG_MISSION_CONTRACT.md](URG_MISSION_CONTRACT.md) § Cloud Forge binding, [URG_CLOUD_PLATFORM.md](../URG_CLOUD_PLATFORM.md).

## Purpose

This contract admits the **Cloud Forge rail scheduler** into AAIS as a governed
performance layer. It selects cognition rails (SAFE / NORMAL / EXPRESS) and emits
`CognitionPlan` artifacts. It does **not** grant execution authority; Jarvis and
Voss remain authoritative for actions and cycle boundaries.

## Naming boundary

| Name | Scope |
|---|---|
| Cloud Forge (this contract) | AAIS cognitive acceleration — rails, plans, caches |
| AAIS Forge contractor | `docs/contracts/FORGE_CONTRACTOR.md` — bounded diff HTTP service |
| Wolf-cog Forge | OS/ISO platform — out of scope for this contract |

## Core law

1. **Law sets the ceiling; rails set speed inside the ceiling.** EXPRESS is never permission to bypass constitutional or proof obligations.
2. **HIGH risk forces SAFE.** No weight vector, cache, or operator preference may downgrade below SAFE when risk is HIGH.
3. **Every rail decision is inspectable.** Outputs include rationale codes traceable in packet metadata or ledger entries.
4. **Claims use labels** `asserted` | `proven` | `rejected` per `REPO_PROOF_LAW.md`.
5. **Caches are law-scoped.** Keys MUST include `tenant_id` and `law_id` (and `law_version` for L1/L2).

## Contract version

```json
{
  "contract_version": "aais.cloud_forge.rail.v1"
}
```

## Enumerations

### Rail

| Value | Meaning |
|---|---|
| `SAFE` | Full verification chain; minimal cache/speculation |
| `NORMAL` | Default trimmed chain |
| `EXPRESS` | Compressed chain; only when risk is not HIGH and weight/law allow |

### Risk level

| Value | Max rail |
|---|---|
| `HIGH` | `SAFE` only |
| `MEDIUM` | `NORMAL` max (EXPRESS forbidden) |
| `LOW` | `EXPRESS` allowed if weight + tenant profile allow |

### Cognition step

| Value | Order (SAFE) | Order (NORMAL) | Order (EXPRESS) |
|---|---|---|---|
| `ANALYZE` | 1 | — | — |
| `PLAN` | 2 | 1 | 1 (fused with TOOLS) |
| `TOOLS` | 3 | 2 | 1 (fused with PLAN) |
| `DRAFT` | 4 | 3 | — |
| `CRITIQUE` | 5 | — | — |
| `FINAL` | 6 | 4 | 2 |

Fused step `PLAN_TOOLS` MAY be emitted as a single step label in traces when rail is EXPRESS.

### Model tier

| Value | Use |
|---|---|
| `tiny` | Routing, classification, low-risk snippets |
| `mid` | Default generation |
| `big` | Novel or high-stakes reasoning (I-bias escalation) |

### Cache mode

| Value | Meaning |
|---|---|
| `off` | No answer/pattern reuse |
| `L0` | Deterministic tool cache only |
| `L1` | L0 + tenant+law answer cache |
| `L2` | L1 + pattern-level CognitionPlan reuse |

### Speculation level

| Value | Meaning |
|---|---|
| `off` | No pre-run tools/retrieval |
| `light` | Pre-fetch read-only context |
| `aggressive` | Parallel tool/retrieval before LLM asks (EXPRESS + high wL only) |

## Rail step chains (normative)

```json
{
  "SAFE": ["ANALYZE", "PLAN", "TOOLS", "DRAFT", "CRITIQUE", "FINAL"],
  "NORMAL": ["PLAN", "TOOLS", "DRAFT", "FINAL"],
  "EXPRESS": ["PLAN_TOOLS", "FINAL"]
}
```

## Schemas

### PerformanceProfile

Tenant or app performance biases. Biases MUST sum to 1.0 ± 0.01.

```json
{
  "latency_bias": 0.4,
  "throughput_bias": 0.3,
  "intelligence_bias": 0.3,
  "wL_express_threshold": 100,
  "wL_express_floor": 50
}
```

| Field | Type | Required | Constraints |
|---|---|---|---|
| `latency_bias` | number | yes | [0, 1] |
| `throughput_bias` | number | yes | [0, 1] |
| `intelligence_bias` | number | yes | [0, 1] |
| `wL_express_threshold` | number | yes | min 0; actor wL must be ≥ this for EXPRESS eligibility |
| `wL_express_floor` | number | yes | min 0; actor wL below this → EXPRESS forbidden |

### GovernanceWeight

```json
{
  "wL": 120,
  "wT": 80,
  "wI": 200,
  "tier": "A"
}
```

| Field | Type | Required | Meaning |
|---|---|---|---|
| `wL` | number | yes | Latency trust — cache, step skip, speculation |
| `wT` | number | Phase 1 optional | Throughput trust — parallelism (default: same as wL) |
| `wI` | number | Phase 1 optional | Intelligence trust — model tier, L1 reuse (default: same as wL) |
| `tier` | string | no | Operator label (`A` \| `B` \| `C`) |

Phase 1 implementations MAY use `wL` only; `wT` and `wI` default to `wL` when omitted.

### LawEnvelope

Admission constraints from constitutional and task law.

```json
{
  "law_id": "meta.architect.v1",
  "law_version": "2026-05-28",
  "forbid_express": false,
  "forbid_cache_above": "L0",
  "forbid_speculation": false,
  "required_proof": false,
  "signals": ["read_only", "docs"]
}
```

| Field | Type | Required | Meaning |
|---|---|---|---|
| `law_id` | string | yes | Active law bundle identifier |
| `law_version` | string | yes | Invalidates caches when changed |
| `forbid_express` | boolean | no | When true, EXPRESS forbidden regardless of risk |
| `forbid_cache_above` | string | no | Cap cache mode: `off` \| `L0` \| `L1` \| `L2` |
| `forbid_speculation` | boolean | no | Forces `speculation: off` |
| `required_proof` | boolean | no | When true, forces SAFE |
| `signals` | string[] | no | Risk rule inputs (see Risk signals) |

### TaskSignature

```json
{
  "task_id": "req-uuid",
  "pattern_class": "docs_explanation",
  "domain": "forge/voss/os_architecture",
  "normalized_prompt_hash": "sha256:…",
  "tool_intents": ["doc_search"],
  "mutation_scope": "none"
}
```

| Field | Type | Required |
|---|---|---|
| `task_id` | string | yes |
| `pattern_class` | string | yes |
| `domain` | string | no |
| `normalized_prompt_hash` | string | no |
| `tool_intents` | string[] | no |
| `mutation_scope` | string | yes — `none` \| `read` \| `write` \| `constitutional` |

### ClusterState (advisory)

```json
{
  "load": "low",
  "hot_domains": ["forge/voss/os_architecture"],
  "model_availability": { "tiny": true, "mid": true, "big": true }
}
```

Implementations MAY pass `{}` in Phase 1.

## Risk signals (v1 rule table)

| Signal / condition | Risk |
|---|---|
| `mutation_scope: constitutional` | HIGH |
| PII, credentials, secrets in prompt or context | HIGH |
| `mutation_scope: write` + prod/deploy paths | HIGH |
| `required_proof: true` | HIGH |
| `mutation_scope: write` (non-constitutional) | MEDIUM |
| External side-effect tools without read-only guarantee | MEDIUM |
| `mutation_scope: read` or `none` + docs/explanation pattern | LOW |

`estimate_novelty` Phase 1: returns MEDIUM always. Phase 2: LOW when pattern hash matches verified ledger entry.

## RailDecision (output)

```json
{
  "contract_version": "aais.cloud_forge.rail.v1",
  "task_id": "req-uuid",
  "rail": "NORMAL",
  "risk": "MEDIUM",
  "novelty": "MEDIUM",
  "rationale_codes": ["risk.medium", "weight.express_denied"],
  "law_ceiling": "NORMAL",
  "claim_status": "asserted",
  "decided_at": "2026-05-28T12:00:00Z"
}
```

| Field | Required | Notes |
|---|---|---|
| `rail` | yes | Final rail after weight + law ceiling |
| `risk` | yes | From `estimate_risk` |
| `novelty` | yes | From `estimate_novelty` |
| `rationale_codes` | yes | Machine-readable audit trail |
| `law_ceiling` | yes | Max rail law allows before weight |
| `claim_status` | yes | `asserted` until proof bundle links decision tests |

### Rationale codes (normative subset)

| Code | Meaning |
|---|---|
| `risk.high` | HIGH risk → SAFE |
| `risk.medium` | MEDIUM risk → NORMAL max |
| `risk.low` | LOW risk → EXPRESS eligible |
| `law.forbid_express` | Law envelope blocked EXPRESS |
| `law.required_proof` | Proof obligation → SAFE |
| `weight.express_granted` | wL + latency_bias allowed faster rail |
| `weight.express_denied` | wL below floor → no EXPRESS |
| `immune.elevated` | Immune protocol forced downgrade |
| `failsafe.force_safe` | Global or operator FORCE_SAFE active |

## CognitionPlan (output)

```json
{
  "contract_version": "aais.cloud_forge.rail.v1",
  "task_id": "req-uuid",
  "rail": "NORMAL",
  "steps": ["PLAN", "TOOLS", "DRAFT", "FINAL"],
  "model_tier": "mid",
  "parallelism": 2,
  "cache_mode": "L0",
  "speculation": "light",
  "domain_template": null,
  "claim_status": "asserted"
}
```

| Field | Constraints |
|---|---|
| `parallelism` | integer 1–16; EXPRESS + high wT may use upper range |
| `cache_mode` | MUST NOT exceed `law_envelope.forbid_cache_above` |
| `speculation` | MUST be `off` if `forbid_speculation` or rail is SAFE |
| `domain_template` | Optional; e.g. `forge/voss/os_architecture` (Phase 2) |

## Selection algorithm (normative)

Implementations MUST follow this order:

1. Compute `risk = estimate_risk(task, law_envelope)`.
2. If `risk == HIGH` OR `law_envelope.required_proof` OR `failsafe.force_safe` → `rail = SAFE`.
3. Else set base: `MEDIUM → NORMAL`, `LOW → EXPRESS`.
4. Apply law ceiling: if `forbid_express` → cap at NORMAL.
5. Apply weight: if `actor.wL < tenant.wL_express_floor` → cap at NORMAL.
6. If `actor.wL >= tenant.wL_express_threshold` AND `tenant.latency_bias >= 0.35` AND `risk != HIGH` → allow min(rail, EXPRESS).
7. Emit `RailDecision` then `build_plan(rail, …)` with cache/speculation capped by law envelope.

## Pipeline integration

Governed direct pipeline traces MAY include:

```json
{
  "rail_decision": { },
  "cognition_plan": { }
}
```

Under packet metadata key `cloud_forge` (Phase 1). Immune protocol responses that are `REROUTE` or `CLAMP` due to rail violations MUST set `rationale_codes` including `immune.elevated`.

## Pattern Ledger admission

Rail decisions MAY be published to the Collective Pattern Ledger when:

- source class: `routing_subsystem`
- event type: `rail_decision`
- evidence: full `RailDecision` + outcome summary
- promotion: subject to `docs/contracts/COLLECTIVE_PATTERN_LEDGER.md` verification gate

Storage path (Phase 2): `docs/proof/cloud-forge/rail-decisions.jsonl`

## Cache layers (Phase 3)

Implementation: `src/cloud_forge/cache.py`.

| Layer | Key scope | Storage |
|---|---|---|
| L0 | `tenant_id` + `law_id` + `law_version` + tool name + input | `.runtime/cloud_forge/cache/L0/` |
| L1 | `hash(tenant, law_id, normalized_question)` + `law_version` in entry | `.runtime/cloud_forge/cache/L1/` |
| L2 | pattern + domain + prompt hash + law scope | `.runtime/cloud_forge/cache/L2/` |

Resolve order on request: L2 → L1 (when `cache_mode` allows). Persist via `store_answer` / `store_plan` in `cloud_forge_context`.

## Cloud locality (Phase 4)

Implementation: `src/cloud_forge/locality.py`, `configs/cloud-forge/domain-slices.json`.

| Concern | API |
|---|---|
| Domain → slice | `resolve_domain_slice(domain)` |
| Weight → queue | `map_governance_to_priority(actor, tenant, cluster)` |
| Session prewarm | `SessionPrewarmStore.resolve_or_create(...)` |
| Placement block | `cloud_placement` on observed bundle |

Tempering: `python -m src.cloud_forge.tempering --dry-run` (see `docs/cloud-forge-tempering-job.md`).

## Violation codes

| Code | HTTP-style severity | Containment |
|---|---|---|
| `rail.law_ceiling_violation` | error | Downgrade to SAFE; log violation |
| `rail.express_forbidden` | error | Reject plan; rebuild as NORMAL |
| `rail.cache_law_mismatch` | error | Invalidate cache entry; SAFE |
| `rail.uninspectable_decision` | error | SAFE; block EXPRESS |
| `rail.contract_version_mismatch` | error | Reject; no rail execution |

## Non-goals

- Replacing Jarvis authorization or Forge contractor boundaries.
- Bypassing `META_ARCHITECT_LAWBOOK` or CI governance gates.
- Cross-tenant cache keys.
- Market, valuation, or unproven latency claims in contract fields.

## Change-of-reality

Any behavioral change MUST update, in one change set or tracked sequence:

1. This contract
2. `docs/cloud-forge-governed-accelerator-program.md`
3. `docs/failsafe/cloud-forge-rail-failsafe.md`
4. Implementation + tests + proof bundle

## Verification (Phase 1 target)

```bash
python -m unittest tests.test_cloud_forge_rails
```

Phase 0 verification: contract + failsafe + backlog present; no implementation claim.
