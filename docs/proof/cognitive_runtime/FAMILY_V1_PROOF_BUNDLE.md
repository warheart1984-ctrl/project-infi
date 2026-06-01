# Nova Cortex v1 — Proof Bundle

**Claim:** Nova Cortex (modular cognitive runtime composition) is implemented and test-covered.

**Status:** `asserted` (single-machine pytest). Cross-machine wolf-cog-os-full boot proof not yet filed.

## Canonical name

**Nova Cortex** — `family_id: nova.cortex`

Constitution: [docs/runtime/NOVA_CORTEX.md](../runtime/NOVA_CORTEX.md)

## Scope

- Shared base: [src/cog_runtime/base.py](../../src/cog_runtime/base.py)
- Decision lobe: [src/cog_runtime/deliberation.py](../../src/cog_runtime/deliberation.py)
- Nova integration: [src/cog_runtime/nova.py](../../src/cog_runtime/nova.py)
- CoG OS bridge: [src/cogos_runtime_bridge.py](../../src/cogos_runtime_bridge.py)
- Wolf payload: [wolf-cog-os/payload/opt/cogos/config/cognitive_runtime_family.json](../../wolf-cog-os/payload/opt/cogos/config/cognitive_runtime_family.json)

## Verification

```bash
pytest tests/test_cog_runtime_base.py tests/test_deliberation_runtime.py tests/test_integration_cog_runtimes.py -q

python -c "from src.cog_runtime import nova_cortex_spec; print(nova_cortex_spec()['name'], nova_cortex_spec()['family_id'])"
```

## Evidence (2026-05-29)

```
family_id: nova.cortex
name: Nova Cortex
pytest: 49 passed (full cog runtime + speaking + jarvis protocol suite)
```

## Anatomy (design)

| Component | Role |
|-----------|------|
| Jarvis Core | Thalamus / router |
| Wolf CoG OS | Constitutional brainstem |
| Speaking Runtime | Prefrontal speech loop |
| Deliberation | Decision lobe |
| Attention | Focus lobe |
| Memory | Hippocampus runtime |
