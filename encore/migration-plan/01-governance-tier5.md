# Unit 01 — governance-tier5

**Status:** migrated  
**Encore service:** `governance/`  
**Contract:** `docs/contracts/AAIS_ADAPTIVE_GOVERNANCE.md` § Self-Auditing (repo root)

## Source behavior

Python `AdaptiveEngine.health_check()` scans genome registry, pending promotions, MP-X proposals, and retirement state; writes:

```
.runtime/governance/tier5_health.json
```

Gate: `make tier5-gate` / `tools/governance/check_adaptive_governance.py`

## Encore endpoint

| Method | Path | Handler |
|--------|------|---------|
| GET | `/governance/tier5/health` | `governance.getTier5Health` |

Returns typed `Tier5HealthReport` — same JSON the Flask stack already produces, without duplicating genome logic in TypeScript.

## Rationale

- **Zero rewrite risk:** Python remains authoritative for governance computation.
- **Immediate value:** Frontends and agents get a stable, documented HTTP contract with Encore-generated OpenAPI.
- **Trace-ready:** Once `encore run` is active, MCP can inspect request latency for this read path.

## Verified locally

```
genome_count: 195
tier5_enabled_genes: 21
stage_histogram: { governed: 179, mvp: 16 }
```

Artifact path: `e:\project-infi\.runtime\governance\tier5_health.json`
