# Nova Cortex on Wolf CoG OS Full

Operator summary for **wolf-cog-os-full** Nova Cortex integration.

Canonical spec (AAIS): [docs/runtime/NOVA_CORTEX_WOLF_INTEGRATION.md](../../docs/runtime/NOVA_CORTEX_WOLF_INTEGRATION.md)

## Edition

- Product: Wolf CoG OS Full Runtime
- Cortex family ID: `nova.cortex`
- Payload manifest: `/opt/cogos/config/cognitive_runtime_family.json`

## Boot vs turn responsibilities

| Phase | Wolf CoG OS | Nova Cortex |
|-------|-------------|-------------|
| Boot | firstboot → governance → spine → observer | Manifest loaded; bridge importable |
| Turn | god_brain + aais pipeline + voice policy | Face → Attention → Deliberation → Speaking |

## Build and export

From repo root:

```bash
bash scripts/cogos/export-cognitive-runtime-family.sh
bash wolf-cog-os/scripts/verify-full-runtime-release.sh
```

Full ISO build: [scripts/build-universal-installer.sh](../scripts/build-universal-installer.sh)

## Lobes in v1.1

| Lobe | Version | Notes |
|------|---------|-------|
| Attention | 1.1 | Focus artifact for every cognitive turn |
| Deliberation | 1.1 | LLM-assisted on companion turns; deterministic fallback |
| Speaking | 1.0 | User-visible narration |
| Memory | 1.0 stub | Activates when memory cues present |

## Operator flags (AAIS chat)

| Flag | Effect |
|------|--------|
| Companion turn | Enables Face → Cortex bridge by default |
| `"cognitive_runtime": true` | Enables cortex on operator turns |
| `"deliberation_llm": true` | LLM-assisted deliberation (companion default) |

## Claim status

**Asserted** until metal boot proof per [METAL_PROOF_CHECKLIST.md](./METAL_PROOF_CHECKLIST.md).
