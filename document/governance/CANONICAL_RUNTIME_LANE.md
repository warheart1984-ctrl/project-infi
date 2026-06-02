# Canonical Runtime Lane

| Field | Value |
|-------|-------|
| **Authority** | [DOCUMENT_SCOPE_LAW.md](./DOCUMENT_SCOPE_LAW.md) · [META_ARCHITECT_LAWBOOK.md](../../META_ARCHITECT_LAWBOOK.md) |
| **Decision** | Option A — repo root `E:/project-infi` is the sole canonical lane |
| **Claim posture** | `asserted` |

## Canonical (editable source)

| Path | Role |
|------|------|
| `src/cog_runtime/` | Nova Cortex / Spark runtime modules |
| `src/cogos_runtime_bridge.py` | Bundle bridge entry |
| `src/aais_composed_runtime.py` | AAIS composed runtime |
| `src/aais_ul.py`, `src/aais_ul_substrate.py` | UL substrate bridge modules |
| `src/direct_challenge_module.py` | Direct challenge module |
| `src/jarvis_reasoning_protocol.py`, `src/jarvis_types.py`, `src/reasoning_types.py` | Reasoning protocol types |
| `src/speaking_runtime/` | Speaking runtime package |

## Generated-only (do not edit directly)

| Path | Mechanism |
|------|-----------|
| `wolf-cog-os/artifacts/synthetic-mind-bundle/` | `scripts/cogos/build_synthetic_mind_bundle.py` |
| `wolf-cog-os/payload/opt/cogos/runtime/src/` | `wolf-cog-os/scripts/stage-nova-cortex-into-payload.sh` |
| `$HOME/.cogos-payload-cache/` | Local forge payload cache |

Promotion flow:

```
src/cog_runtime  →  build_synthetic_mind_bundle  →  wolf payload / ISO inject
```

## Non-canonical (must not exist in worktree)

- `AAIS-main/`, `Aris--main/`, `Project-Infinity-main/` — duplicate import mirrors
- `aris/` — sidecar copy
- Root-level `opt/cogos/` or `.synthetic-mind-bundle-build/` outside allowed paths

## Enforcement

- `make synthetic-mind-gate` runs `check-canonical-lane-sync.py`
- `make repo-hygiene-gate` runs `check-repo-hygiene.py`
- `wolf-cog-os/.gitignore` excludes generated payload runtime tree

## Related

- [SYNTHETIC_MIND.md](../../docs/runtime/SYNTHETIC_MIND.md)
- [REPO_HYGIENE_MANIFEST.json](../../docs/audit/REPO_HYGIENE_MANIFEST.json)
