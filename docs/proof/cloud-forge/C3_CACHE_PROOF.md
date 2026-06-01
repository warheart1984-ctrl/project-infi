# Cloud Forge Phase 3 Proof Packet

Claim: Law-scoped L0–L2 caches are **complete** and integrated with Cloud Forge scheduling.

Claim status: **proven** (37 unit tests Phase 1–3, Python 3.12, exit 0).

## Scope

| ID | Deliverable | Path |
|---|---|---|
| C3-1 | L0 tenant+law tool cache | `src/cloud_forge/cache.py`, `cache_bridge.py`, `app/tools.py` |
| C3-2 | L1 answer cache KV | `src/cloud_forge/cache.py` (`l1_get` / `l1_set`) |
| C3-3 | L2 pattern cache | `src/cloud_forge/cache.py` (`l2_get` / `l2_set`) |
| C3-4 | Integration | `src/cloud_forge/integration.py` (`resolve_cache`, `persist_cache_outcomes`) |

## Key rules (proven in tests)

- Cache keys include `tenant_id` + `law_id`; entries store `law_version` and reject mismatches.
- L1 key material: `hash(tenant, law_id, normalized_question)`.
- L2 stores full `CognitionPlan` per pattern + domain + prompt hash.
- `forbid_cache_above` caps plan `cache_mode` before resolve.
- Cross-tenant reads return miss (no leak).

## Verification

```bash
py -3.12 -m unittest tests.test_cloud_forge_rails tests.test_cloud_forge_phase2 tests.test_cloud_forge_phase3 -v
```

## L0 bridge (optional)

Set env for `app/tools.py` deterministic tools:

- `CLOUD_FORGE_TENANT_ID`
- `CLOUD_FORGE_LAW_ID`
- `CLOUD_FORGE_LAW_VERSION`
- `CLOUD_FORGE_CACHE_ROOT` (optional)

## Store after response

```json
"cloud_forge_context": {
  "store_answer": "…",
  "store_plan": true,
  "normalized_question": "sha256:…"
}
```

## Next gate

Phase 4: cloud locality (deferred).
