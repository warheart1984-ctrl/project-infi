# Civilizational Arc — Operator Rollback (Stages 15–18)

CISIV stage: **verification**

Documents **operator rollback** for adopted civilizational overlays (Releases **45–48**). No new API is required; rollback is registry + memory-board overlay surgery with observe verification.

## Per-tier rollback map

| Tier | Release | Governance registry | Memory-board overlay | Python query | HTTP verification |
|------|---------|---------------------|----------------------|--------------|-------------------|
| ISD | 45 | `governance/operator_diplomatic_registry.v1.json` | `{AAIS_RUNTIME_DIR}/jarvis_memory_board_diplomacy.v1.json` | `adopted_accords(repo_root=...)` | `GET /api/operator/diplomacy/accords` |
| NFD | 46 | `governance/operator_norm_federation_registry.v1.json` | `{AAIS_RUNTIME_DIR}/jarvis_memory_board_norm_federation.v1.json` | `adopted_treaties(repo_root=...)` | `GET /api/operator/norm-federations/treaties` |
| CEV | 47 | `governance/operator_constitutional_evolution_registry.v1.json` | `{AAIS_RUNTIME_DIR}/jarvis_memory_board_constitutional_evolution.v1.json` | `adopted_amendments(repo_root=...)` | `GET /api/operator/constitutional-evolution/amendments` |
| GCV | 48 | `governance/operator_civilization_registry.v1.json` | `{AAIS_RUNTIME_DIR}/jarvis_memory_board_civilization.v1.json` | `adopted_civilizations(repo_root=...)` | `GET /api/operator/civilizations/charters` |

Default `AAIS_RUNTIME_DIR` when unset: repository `.runtime/aais-data` (see each runtime module).

## Rollback procedure (operator)

1. **Identify** the adopted artifact ID (`accord_id`, `treaty_id`, `amendment_id`, or `civilization_id`) from the registry JSON or operator GET route.
2. **Remove** the entry from the governance registry list (`accords`, `treaties`, `amendments`, or `civilizations` array). Preserve `operator_*_registry_version` unchanged.
3. **Sync overlay:** open the matching memory-board overlay JSON under `AAIS_RUNTIME_DIR` and remove the same ID from the overlay’s adopted list (or delete the overlay file if it becomes empty). Runtimes merge registry + overlay on the next observe/adopt cycle.
4. **Verify:** run observe for the tier (`observe_*_drift` / operator observe POST) and confirm counts drop; drift posture should reflect absence of the rolled-back artifact.
5. **Optional HTTP check:** GET the accords/treaties/amendments/charters route; adopted list length must match registry.

## Automated analogue (pytest)

Adopt tests use isolated temp `repo_root` + empty or copied registries; tearDown removes temp dirs — the same logical steps as operator rollback without touching production JSON:

| Test module | Demonstrates |
|-------------|--------------|
| `tests/test_inter_substrate_diplomacy_adopt.py` | Dual-gate adopt → registry count + overlay file |
| `tests/test_norm_federation_adopt.py` | Treaty adopt with `norm_a` / `norm_b` |
| `tests/test_constitutional_evolution_adopt.py` | Amendment adopt with Jarvis receipt |
| `tests/test_governed_civilization_adopt.py` | Civilization adopt with multi-charter IDs |

Observe tests (`test_*_observe.py`) assert **GCV-0 / ISD-0 / … observe does not write overlay** until adopt — rollback to “observe-only” posture is verifiable by absence of overlay file after registry cleanup.

## Safety notes

- Do not delete registry version keys or schema fields; only remove adopted rows.
- Chaos-hammer injected accords in a shared mock runtime should be rolled back the same way before pilot sign-off (see `FEDERATION_CHAOS_RUN_2026-06-07.md`).
- Dual-gate adoption remains blocked without `operator_approved` and Jarvis authorization (`inter_substrate_diplomacy_runtime.py` and sibling runtimes return 403).

## Related

- Sign-off: [`CIVILIZATIONAL_ARC_PROVEN_SIGNOFF.md`](./CIVILIZATIONAL_ARC_PROVEN_SIGNOFF.md)
- Pilot evidence: [`CIVILIZATIONAL_ARC_PILOT_EVIDENCE_2026-06-07.md`](./CIVILIZATIONAL_ARC_PILOT_EVIDENCE_2026-06-07.md)
