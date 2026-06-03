# Linguistic Snapshots

Append-only checkpoints of mythic and engineering linguistic layers per subsystem gene.

## Purpose

Hybrid history for [linguistic diff](../../tools/linguistic_diff.py):

- **Snapshots** (this directory) — captured on `make naming-genome-gate` when fingerprints change
- **Git** — older transitions reconstructed from commit history on genome-linked paths

## Layout

```text
governance/linguistic_snapshots/<gene>/<ISO8601Z>.json
```

Schema: [schemas/linguistic_snapshot.v1.json](../../schemas/linguistic_snapshot.v1.json)

## Policy

- Do not edit snapshot files by hand; regenerate via naming-genome-gate
- Commit new snapshots when linguistic layers change (MP-X, SSP admission, Wave 2 header adds)
- Bump `ssp.linguistic_version` in the subsystem genome when mythic or engineering text changes

## Related

- [AAIS_CODEX_CURSOR_NAMING_PROTOCOL.md](../../docs/contracts/AAIS_CODEX_CURSOR_NAMING_PROTOCOL.md)
- [legacy_engineering_aliases.v1.json](../legacy_engineering_aliases.v1.json)
