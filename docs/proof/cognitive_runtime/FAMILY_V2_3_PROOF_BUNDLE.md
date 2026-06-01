# Nova Cortex v2.3 — Proof Bundle

**Claim:** Execution v1.2 (tiered recovery + safe rollback), Planning v1.3 (adaptive chain selection), Arcs v1.3 (parent/child goal closure), and Tuning v1.1 (bounded history + drift guard) are implemented and test-covered under Nova Cortex v2.3.

**Status:** `asserted` (single-machine pytest). Cross-machine wolf boot proof not yet filed.

## Scope

| Deliverable | Path |
|-------------|------|
| Execution v1.2 | [src/cog_runtime/execution.py](../../src/cog_runtime/execution.py) |
| Planning v1.3 | [src/cog_runtime/planning.py](../../src/cog_runtime/planning.py) |
| Arcs v1.3 | [src/cog_runtime/arcs.py](../../src/cog_runtime/arcs.py) |
| Tuning v1.1 | [src/cog_runtime/tuning.py](../../src/cog_runtime/tuning.py) |
| Nova wiring | [src/cog_runtime/nova.py](../../src/cog_runtime/nova.py) |
| v3 roadmap | [docs/runtime/NOVA_CORTEX_V3_ROADMAP.md](../../docs/runtime/NOVA_CORTEX_V3_ROADMAP.md) |
| Payload manifest | [wolf-cog-os/payload/opt/cogos/config/cognitive_runtime_family.json](../../wolf-cog-os/payload/opt/cogos/config/cognitive_runtime_family.json) |

## Verification

```bash
pytest tests/test_attention_runtime.py tests/test_deliberation_runtime.py tests/test_deliberation_llm.py tests/test_memory_runtime.py tests/test_reflection_runtime.py tests/test_planning_runtime.py tests/test_execution_runtime.py tests/test_tuning.py tests/test_cortex_arcs.py tests/test_integration_cog_runtimes.py tests/test_nova_face_bridge.py -q

python -c "from src.cog_runtime import nova_cortex_spec; s=nova_cortex_spec(); print(s['version'], s['family_id'])"

python -m src.cogos_runtime_bridge --validate-config wolf-cog-os/payload/opt/cogos/config/cognitive_runtime_family.json

python .github/scripts/check-nova-cortex-governance.py
```

## Lobe contracts (v2.3)

**Execution artifact:** adds `recovery_paths`, `recovery_tier`, `rollback_policy`, `rollback_safe`; rollback skips partial passes, same targets, and repeat rollbacks

**Planning artifact:** adds `chain_scores`, `chain_selection_reason`; adaptive chain pick from arc + tuning evidence

**Cortex arc:** adds `closed_subgoals`, `goal_closure_status`; hierarchy nodes carry `goal_id`, `parent_id`, `status`

**Tuning artifact:** adds `tuning_history` (max 8), `drift_guarded`, `drift_score`

## Debt

- Cross-machine wolf-cog-os-full companion arc + safe rollback on installed ISO
- Nova Cortex v3.0 persistent cognitive identity (see roadmap; not in this bundle)
