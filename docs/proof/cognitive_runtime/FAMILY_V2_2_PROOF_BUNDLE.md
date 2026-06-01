# Nova Cortex v2.2 — Proof Bundle

**Claim:** Execution v1.1 (recovery + rollback), Planning v1.2 (multi-step chains), Arcs v1.2 (hierarchical goals), and Cortex v2.2 self-tuning invariants are implemented and test-covered.

**Status:** `asserted` (single-machine pytest). Cross-machine wolf boot proof not yet filed.

## Scope

| Deliverable | Path |
|-------------|------|
| Execution v1.1 | [src/cog_runtime/execution.py](../../src/cog_runtime/execution.py) |
| Planning v1.2 | [src/cog_runtime/planning.py](../../src/cog_runtime/planning.py) |
| Arcs v1.2 | [src/cog_runtime/arcs.py](../../src/cog_runtime/arcs.py) |
| Self-tuning | [src/cog_runtime/tuning.py](../../src/cog_runtime/tuning.py) |
| Nova wiring | [src/cog_runtime/nova.py](../../src/cog_runtime/nova.py) |
| Payload manifest | [wolf-cog-os/payload/opt/cogos/config/cognitive_runtime_family.json](../../wolf-cog-os/payload/opt/cogos/config/cognitive_runtime_family.json) |

## Verification

```bash
pytest tests/test_attention_runtime.py tests/test_deliberation_runtime.py tests/test_deliberation_llm.py tests/test_memory_runtime.py tests/test_reflection_runtime.py tests/test_planning_runtime.py tests/test_execution_runtime.py tests/test_tuning.py tests/test_cortex_arcs.py tests/test_integration_cog_runtimes.py tests/test_nova_face_bridge.py -q

python -c "from src.cog_runtime import nova_cortex_spec; s=nova_cortex_spec(); print(s['version'], s['family_id'])"

python -m src.cogos_runtime_bridge --validate-config wolf-cog-os/payload/opt/cogos/config/cognitive_runtime_family.json
```

## Lobe contracts (v2.2)

**Planning artifact:** adds `step_chains`, `active_chain_id`, `active_chain`, `chain_step_index`

**Execution artifact:** adds `recovery_action`, `recovered`, `rollback_target`, `rollback_applied`; stages include recover and rollback

**Cortex arc:** adds `root_goal`, `subgoals`, `current_subgoal`, `goal_hierarchy`

**Tuning artifact:** `tuned_thresholds`, `adjustments`, `tuning_generation` on `session.metadata["cortex_invariant_tuning"]`

## Debt

- Cross-machine wolf-cog-os-full companion arc + execution recovery/rollback on installed ISO
- On-device `runtime.cognitive_runtime_family` Python loader in payload cache
