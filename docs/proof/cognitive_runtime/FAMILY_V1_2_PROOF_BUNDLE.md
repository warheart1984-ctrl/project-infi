# Nova Cortex v1.2 — Proof Bundle

**Claim:** Attention v1.2 (multi-focus + salience), Deliberation v1.2 (multi-criteria scoring), Memory v1.0 (full encode/index/retrieve/forget), Reflection v1.0 (cross-lobe loop), and cortex orchestration are implemented and test-covered.

**Status:** `asserted` (single-machine pytest). Cross-machine wolf boot proof not yet filed.

## Scope

| Deliverable | Path |
|-------------|------|
| Attention v1.2 | [src/cog_runtime/attention.py](../../src/cog_runtime/attention.py) |
| Deliberation v1.2 | [src/cog_runtime/deliberation.py](../../src/cog_runtime/deliberation.py) |
| Deliberation LLM | [src/cog_runtime/deliberation_llm.py](../../src/cog_runtime/deliberation_llm.py) |
| Memory v1.0 | [src/cog_runtime/memory.py](../../src/cog_runtime/memory.py) |
| Reflection v1.0 | [src/cog_runtime/reflection.py](../../src/cog_runtime/reflection.py) |
| Nova wiring | [src/cog_runtime/nova.py](../../src/cog_runtime/nova.py), [nova_face.py](../../src/cog_runtime/nova_face.py) |
| Wolf integration (canonical) | [docs/runtime/NOVA_CORTEX_WOLF_INTEGRATION.md](../runtime/NOVA_CORTEX_WOLF_INTEGRATION.md) |
| Wolf integration (OS) | [wolf-cog-os/docs/NOVA_CORTEX_INTEGRATION.md](../../wolf-cog-os/docs/NOVA_CORTEX_INTEGRATION.md) |
| Payload manifest | [wolf-cog-os/payload/opt/cogos/config/cognitive_runtime_family.json](../../wolf-cog-os/payload/opt/cogos/config/cognitive_runtime_family.json) |

## Verification

```bash
pytest tests/test_attention_runtime.py tests/test_deliberation_runtime.py tests/test_deliberation_llm.py tests/test_memory_runtime.py tests/test_reflection_runtime.py tests/test_integration_cog_runtimes.py tests/test_nova_face_bridge.py -q

python -c "from src.cog_runtime import nova_cortex_spec; s=nova_cortex_spec(); print(s['version'], s['family_id'])"

python -m src.cogos_runtime_bridge --validate-config wolf-cog-os/payload/opt/cogos/config/cognitive_runtime_family.json
```

## Lobe contracts (v1.2)

**FocusArtifact:** `primary_focus`, `secondary_focus`, `focus_signals`, `weights`, `salience`, `signal_sources`, `frame_kind`, `suppressed`

**Decision object:** `chosen_option`, `alternatives`, `rationale`, `assumptions`, `tradeoffs`, `criteria_scores`, `winning_criteria`, `commit_source`

**Memory artifact:** `encoded`, `index_keys`, `retrieved_cues`, `forgotten_advisory`

**Reflection artifact:** `expected_outcome`, `alignment`, `gaps`, `adjustments`, `next_turn_hints`

## Debt

- Cross-machine wolf-cog-os-full companion turn on installed ISO
- On-device `runtime.cognitive_runtime_family` Python loader in payload cache (documented seam only)
