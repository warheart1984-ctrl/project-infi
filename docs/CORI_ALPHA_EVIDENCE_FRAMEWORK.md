# CORI Alpha Evidence Framework

CORI Alpha treats the governed runtime as an **evidence factory**: every meaningful event becomes structured, queryable continuity evidence with hash, timestamp, and chainable foreign keys.

## Core evidence classes

| Class | Source | Event types | Store |
|-------|--------|-------------|-------|
| **Identity** | Identity Service, `identity_bridge`, HUD snapshots | `identity_snapshot`, `user_created`, `steward_role_assigned` | `identity_snapshots` + `continuity_events` |
| **Asset** | Asset Registry (`src/cori/asset_registry.py`) | `asset_created`, `asset_updated`, `asset_linked_to_evidence` | `assets` + `continuity_events` |
| **Evidence artifacts** | Evidence Engine / governed spine | `evidence_attached`, `evidence_hashed`, `evidence_verified` | `continuity_events` |
| **Validation** | Law kernel, URG, validation layer | `law_eval`, `validation_requested`, `validation_decided`, `urg_mission` | `continuity_events` |
| **Execution** | AAES, Nexus module | `aaes_exec`, `nexus_event` | `continuity_events` + Nexus JSONL ledger |
| **Reflexive / governance** | Panels (reflexive, steward, perception) | `panel_emitted` | `panels` (`panel_store.sqlite3`) + `continuity_events` |

## Implementation

- **Emitter:** `src/cori/evidence_factory.py` — `EvidenceFactory`, `EvidenceEnvelope`, `hash_evidence_payload()`
- **Write-through:** `src/governed/persistence.py` calls the factory on every governed mission completion
- **Asset registry:** `src/cori/asset_registry.py` — mission-scoped assets (`asset:mission:{mission_id}`)

## Evidence envelope shape

Each continuity row stores a canonical envelope:

```json
{
  "evidence_id": "ev-…",
  "evidence_class": "validation",
  "event_type": "law_eval",
  "payload": { },
  "payload_hash": "sha256…",
  "recorded_at": "2026-06-19T…Z",
  "steward_identity": "steward-demo",
  "asset_id": "asset:mission:…",
  "law_eval_id": "…",
  "mission_id": "…",
  "execution_id": "…",
  "nexus_event_id": "…",
  "introduced_by": "nova"
}
```

## Design principles

1. **Write-through on emit** — evidence is persisted at the moment the runtime event occurs, not batched later.
2. **Hash + timestamp** — `payload_hash` is recomputable from canonical JSON; `recorded_at` is UTC ISO-8601.
3. **Chainable** — foreign keys (`asset_id`, `law_eval_id`, `mission_id`, `execution_id`) reconstruct:
   `identity → asset → evidence → validation → execution → nexus`
4. **Governance-aware** — steward identity, law provenance (`introduced_by`), and mission linkage are first-class envelope fields.

## Governed mission evidence chain

On `make_governed_mission()` completion:

1. `identity_snapshot`
2. `asset_created` for `asset:mission:{mission_id}`
3. `evidence_attached` + `evidence_hashed` (law eval artifact)
4. `validation_requested` + `validation_decided`
5. `law_eval`, `urg_mission`, `aaes_exec`, `nexus_event`
6. `panel_emitted` for reflexive and steward panels

## SQLite stores

| File | Schema fixture | Env override |
|------|----------------|--------------|
| `data/continuity.sqlite3` | `fixtures/continuity/continuity.sql` | `CONTINUITY_STORE_PATH` |
| `data/nova_panel_store.sqlite3` | `fixtures/continuity/panel_store.sql` | `NOVA_PANEL_STORE_PATH` |
| `data/law-ledger.sqlite3` | `fixtures/continuity/law_ledger.sql` | `LAW_LEDGER_PATH` |

## Related

- Runtime invariants: `tests/test_runtime_governance_invariants.py`
- Dashboard API: `docs/CORI_ALPHA_OBSERVABILITY_DASHBOARD.md`
- Stewardship alignment: `docs/CORI_ALPHA_STEWARDSHIP_RUNTIME_ALIGNMENT.md`
