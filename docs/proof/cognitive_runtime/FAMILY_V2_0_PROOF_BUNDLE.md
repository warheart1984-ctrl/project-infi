# Nova Cortex v2.0 — Proof Bundle

**Claim:** Reflection v1.3 → Planning loop, Memory v1.1 episodic/semantic split, and Cortex v2.0 multi-turn arcs are implemented and test-covered.

**Status:** `asserted` (single-machine pytest). Cross-machine wolf boot proof not yet filed.

## Scope

| Deliverable | Path |
|-------------|------|
| Reflection v1.3 | [src/cog_runtime/reflection.py](../../src/cog_runtime/reflection.py) |
| Planning v1.0 | [src/cog_runtime/planning.py](../../src/cog_runtime/planning.py) |
| Memory v1.1 | [src/cog_runtime/memory.py](../../src/cog_runtime/memory.py) |
| Cortex arcs v2.0 | [src/cog_runtime/arcs.py](../../src/cog_runtime/arcs.py) |
| Nova wiring | [src/cog_runtime/nova.py](../../src/cog_runtime/nova.py) |
| Payload manifest | [wolf-cog-os/payload/opt/cogos/config/cognitive_runtime_family.json](../../wolf-cog-os/payload/opt/cogos/config/cognitive_runtime_family.json) |

## Verification

```bash
pytest tests/test_attention_runtime.py tests/test_deliberation_runtime.py tests/test_deliberation_llm.py tests/test_memory_runtime.py tests/test_reflection_runtime.py tests/test_planning_runtime.py tests/test_cortex_arcs.py tests/test_integration_cog_runtimes.py tests/test_nova_face_bridge.py -q

python -c "from src.cog_runtime import nova_cortex_spec; s=nova_cortex_spec(); print(s['version'], s['family_id'])"

python -m src.cogos_runtime_bridge --validate-config wolf-cog-os/payload/opt/cogos/config/cognitive_runtime_family.json
```

## Lobe contracts (v2.0)

**Reflection artifact:** adds `planning_handoff: boolean`

**Planning artifact:** `arc_step`, `steps`, `checkpoints`, `handoff_summary`, `next_action`

**Memory artifact:** `episodic_records`, `semantic_records`, `retrieved_episodic`, `retrieved_semantic`

**Cortex arc:** `arc_id`, `goal`, `status`, `turn_count`, `turns[]`, `open_threads[]`, `closed_threads[]`

## Debt

- Cross-machine wolf-cog-os-full companion arc continuity on installed ISO
- On-device `runtime.cognitive_runtime_family` Python loader in payload cache
