# Wolf CoG OS Forge Layout

Staged to `/forge` on Forge ISO builds. This is the self-hosting OS factory cockpit.

## Layout

- `pipelines/` — variant pipeline specs (YAML)
- `templates/` — base configs and skeletons
- `overlays/` — file trees layered onto rootfs
- `scripts/` — pipeline runners and staged build wrappers
- `governance/` — sigil/invariant profile references
- `output/` — built ISOs, logs, signatures
- `cache/` — package and rootfs cache (optional)

## Operator entrypoints

- Boot menu: **Enter Forge Mode** (`cogos.forge=1`)
- CLI menu: `forge-menu`
- Direct run: `forge-run-pipeline.sh /forge/pipelines/daily-driver.yaml`
