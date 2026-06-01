# Nova Cortex v1.1 — Proof Bundle

**Claim:** Attention lobe v1.1, Deliberation lobe v1.1 (LLM-assisted + deterministic fallback), and Wolf integration docs are implemented and test-covered.

**Status:** `asserted` (single-machine pytest). Cross-machine wolf boot proof not yet filed.

## Scope

| Deliverable | Path |
|-------------|------|
| Attention v1.1 | [src/cog_runtime/attention.py](../../src/cog_runtime/attention.py) |
| Deliberation v1.1 | [src/cog_runtime/deliberation.py](../../src/cog_runtime/deliberation.py) |
| Deliberation LLM | [src/cog_runtime/deliberation_llm.py](../../src/cog_runtime/deliberation_llm.py) |
| Nova wiring | [src/cog_runtime/nova.py](../../src/cog_runtime/nova.py), [nova_face.py](../../src/cog_runtime/nova_face.py) |
| Wolf integration (canonical) | [docs/runtime/NOVA_CORTEX_WOLF_INTEGRATION.md](../runtime/NOVA_CORTEX_WOLF_INTEGRATION.md) |
| Wolf integration (OS) | [wolf-cog-os/docs/NOVA_CORTEX_INTEGRATION.md](../../wolf-cog-os/docs/NOVA_CORTEX_INTEGRATION.md) |
| Payload manifest | [wolf-cog-os/payload/opt/cogos/config/cognitive_runtime_family.json](../../wolf-cog-os/payload/opt/cogos/config/cognitive_runtime_family.json) |

## Verification

```bash
pytest tests/test_attention_runtime.py tests/test_deliberation_runtime.py tests/test_deliberation_llm.py tests/test_integration_cog_runtimes.py tests/test_nova_face_bridge.py -q

python -c "from src.cog_runtime import nova_cortex_spec; s=nova_cortex_spec(); print(s['version'], s['family_id'])"

python -m src.cogos_runtime_bridge --validate-config wolf-cog-os/payload/opt/cogos/config/cognitive_runtime_family.json
```

## Evidence

```
pytest: 24+ passed (attention, deliberation, deliberation_llm, integration, nova_face_bridge)
family_id: nova.cortex
cortex version: 1.1
attention runtime version: 1.1
deliberation runtime version: 1.1
```

## Lobe contracts (v1.1)

**FocusArtifact:** `primary_focus`, `focus_signals` (max 3), `weights`, `frame_kind`, `suppressed`

**Decision object:** `chosen_option`, `alternatives`, `rationale`, `assumptions`, `tradeoffs`, `commit_source`

## Debt

- Cross-machine wolf-cog-os-full companion turn on installed ISO
- On-device `runtime.cognitive_runtime_family` Python loader in payload cache (documented seam only)
