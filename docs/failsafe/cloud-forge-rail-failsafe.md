# Cloud Forge Rail Failsafe

Status: **active** (Phase 0).

Authority: `META_ARCHITECT_LAWBOOK.md` Doctrine IV (Failsafe), `docs/contracts/cloud-forge-rail-contract.md`.

Program: `docs/cloud-forge-governed-accelerator-program.md`.

## Purpose

Define fail-safe defaults, operator controls, containment, and recovery when the
Cloud Forge rail scheduler misclassifies risk, serves stale cache, or conflicts
with immune protocol or constitutional law.

## Safe defaults

| Control | Default | Rationale |
|---|---|---|
| Rail when scheduler unavailable | `SAFE` | Unknown risk → full chain |
| Cache mode when law unknown | `off` | No unscoped reuse |
| Speculation | `off` | No pre-run side effects until explicitly enabled |
| EXPRESS | forbidden | Until risk LOW + weight + law allow |
| New tenant session | `NORMAL` max first N requests | N=10 (configurable Phase 1) |

## Kill switches

### FORCE_SAFE (global)

**Effect:** All requests receive `rail: SAFE` regardless of weight or cache.

**Activation:**

- Operator env: `CLOUD_FORGE_FORCE_SAFE=1`
- Or runtime flag file: `.runtime/cloud_forge/force_safe` (presence = on)

**Deactivation:** Remove env var or flag file; restart not required if hot-reload supported (Phase 1+).

**Audit:** Every forced decision MUST log `rationale_codes: ["failsafe.force_safe"]`.

### EXPRESS_KILL (tenant or global)

**Effect:** Cap all rails at `NORMAL`; EXPRESS forbidden.

**Activation:** `CLOUD_FORGE_EXPRESS_KILL=1` or per-tenant list in `.runtime/cloud_forge/express_kill.json`.

**Use when:** Suspected cache poisoning, model drift, or unreviewed EXPRESS template.

### CACHE_FLUSH

**Effect:** Invalidate L1/L2 for scope (tenant, law_id, or global). L0 included on global flush.

**Activation (Phase 3 implemented):**

- Global: create file `.runtime/cloud_forge/cache_flush.all` (removed automatically on next cache access)
- Tenant: create file `.runtime/cloud_forge/cache_flush.<tenant_id>`
- Programmatic: `CloudForgeCacheStore().flush(tenant_id=..., layers=("L1", "L2"))`

**Recovery:** Next request rebuilds from SAFE or NORMAL; no EXPRESS until re-warmed.

## Automatic downgrade triggers

| Trigger | Action | Rationale code |
|---|---|---|
| Immune `REROUTE` / `REJECT` / `QUARANTINE` on rail path | Next decision SAFE; current plan aborted | `immune.elevated` |
| `law_version` change mid-session | Flush L1/L2 for tenant+law; cap cache at L0 | `rail.cache_law_mismatch` |
| Stream governance violation (Voss / content filter) | Cut stream; SAFE for retry | `rail.stream_violation` |
| Missing `law_envelope` | SAFE; cache off | `rail.uninspectable_decision` |
| Contract version mismatch | No rail execution; Jarvis handoff | `rail.contract_version_mismatch` |
| Constitutional / proof-law edit task detected | SAFE only | `risk.high` |

## Cache poison handling

1. **Detect:** L1 answer fails verification, law_id mismatch, or cross-tenant key leak (implementation MUST reject at key construction).
2. **Contain:** Set `CACHE_FLUSH` for affected tenant+law_id; enable `EXPRESS_KILL` for tenant if repeat offense.
3. **Recover:** Serve from SAFE; log incident to Pattern Ledger as `failure` or `near_miss`.
4. **Prove:** Trust bundle with flush scope + before/after hashes before re-enabling EXPRESS.

## Operator override

Operators MAY force rail via governed handoff (Jarvis authority required):

| Override | Requires | Logged field |
|---|---|---|
| Force SAFE | operator id + reason | `operator_override.force_safe` |
| Force NORMAL | operator id + reason | `operator_override.force_normal` |
| Allow EXPRESS (one-shot) | Meta Architect or delegated tier A + reason | `operator_override.allow_express` |

Overrides MUST NOT bypass:

- HIGH risk classification for constitutional edits
- Proof obligations when `required_proof: true`
- Forge contractor / lane guardrails

Overrides expire after single request unless renewed.

## Rollback and recovery

### Per-request rollback

- Abort in-flight EXPRESS plan → re-queue as NORMAL with cache off.
- No partial external effects without Voss Λ completion check.

### Session rollback

- Disable EXPRESS for session; flush L1/L2 for session tenant.
- Replay last N rail decisions from `docs/proof/cloud-forge/rail-decisions.jsonl` (Phase 2).

### Post-incident

1. FORCE_SAFE until root cause classified.
2. Update contract or risk table if misclassification confirmed.
3. Proof bundle: `docs/proof/cloud-forge/INCIDENT_<date>.md`
4. Meta Architect sign-off before EXPRESS re-enabled globally.

## Escalation

| Severity | Escalate to | When |
|---|---|---|
| S1 | Operator | Single failed EXPRESS; auto-downgrade succeeded |
| S2 | Meta Architect | Repeated cache law mismatch or immune quarantine |
| S3 | Meta Architect + halt EXPRESS globally | Constitutional bypass attempt or cross-tenant cache leak |

## Monitoring signals (Phase 1+)

- Rate of `failsafe.force_safe` per hour
- EXPRESS share vs NORMAL/SAFE
- `rail.cache_law_mismatch` count
- Immune `immune.elevated` correlated with rail domain

Alerts are **proven** — wired to Infinity-1 operator dashboard (`infinity1-monitoring-alerts` panel; `GET /api/operator/dashboard/monitoring`).

## Related surfaces

- Immune: `docs/contracts/AAIS_IMMUNE_PROTOCOL.md`
- Pattern Ledger: `docs/contracts/COLLECTIVE_PATTERN_LEDGER.md`
- Voss binding: `voss_binding.py` (cycle boundary after mutations)
- Wolf-cog Forge failsafe: separate OS pipeline — do not conflate

## Change-of-reality

Failsafe changes MUST ship with contract updates and verification paths per
`cloud-forge-rail-contract.md` § Change-of-reality.
