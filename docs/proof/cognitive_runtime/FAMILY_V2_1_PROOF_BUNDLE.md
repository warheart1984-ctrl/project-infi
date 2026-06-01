# Nova Cortex v2.1 — Proof Bundle

**Claim:** Planning v1.1 → Execution loop, Memory v1.2 episodic compression/semantic abstraction, and Arcs v1.1 goal-typed multi-turn continuity are implemented and test-covered.

**Status:** `asserted` (single-machine pytest). Cross-machine wolf boot proof not yet filed.

## Scope

| Deliverable | Path |
|-------------|------|
| Planning v1.1 | [src/cog_runtime/planning.py](../../src/cog_runtime/planning.py) |
| Execution v1.0 | [src/cog_runtime/execution.py](../../src/cog_runtime/execution.py) |
| Memory v1.2 | [src/cog_runtime/memory.py](../../src/cog_runtime/memory.py) |
| Arcs v1.1 | [src/cog_runtime/arcs.py](../../src/cog_runtime/arcs.py) |
| Nova wiring | [src/cog_runtime/nova.py](../../src/cog_runtime/nova.py) |
| Payload manifest | [wolf-cog-os/payload/opt/cogos/config/cognitive_runtime_family.json](../../wolf-cog-os/payload/opt/cogos/config/cognitive_runtime_family.json) |

## Verification

```bash
pytest tests/test_attention_runtime.py tests/test_deliberation_runtime.py tests/test_deliberation_llm.py tests/test_memory_runtime.py tests/test_reflection_runtime.py tests/test_planning_runtime.py tests/test_execution_runtime.py tests/test_cortex_arcs.py tests/test_integration_cog_runtimes.py tests/test_nova_face_bridge.py -q

python -c "from src.cog_runtime import nova_cortex_spec; s=nova_cortex_spec(); print(s['version'], s['family_id'])"

python -m src.cogos_runtime_bridge --validate-config wolf-cog-os/payload/opt/cogos/config/cognitive_runtime_family.json
```

## Lobe contracts (v2.1)

**Planning artifact:** adds `execution_handoff: boolean`

**Execution artifact:** `bound_action`, `executed_steps`, `verification_status`, `report`, `execution_complete`

**Memory artifact:** adds `compressed_episodic`, `semantic_abstractions`

**Cortex arc:** adds `goal_type` (`decision|continuity|exploration|repair|general`), `arc_version`

## Debt

- Cross-machine wolf-cog-os-full companion arc + execution verification on installed ISO
- On-device `runtime.cognitive_runtime_family` Python loader in payload cache
