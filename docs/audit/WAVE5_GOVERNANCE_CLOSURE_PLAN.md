# Wave 5 Governance Closure Plan — 2026-06-06

CISIV stage: **verification**

Companion to [SEAM_STRESS_RUN_2026-06-06.md](./SEAM_STRESS_RUN_2026-06-06.md) and [AAIS_FLAGSHIP_AUDIT_2026-06-06.md](./AAIS_FLAGSHIP_AUDIT_2026-06-06.md).

## Purpose

Close **Wave 5** governance gate seams from the Full Live Seam Stress plan. Runtime Waves 1–4 are already green (187 probes, 0 failures). Wave 5 unblocks full Infinity-1 flagship GA sign-off.

## Baseline re-verify (2026-06-06 rerun)

Commands executed on workspace:

```bash
python tools/governance/check_subsystem_genome.py
python tools/naming_protocol_lint.py
python tools/governance/alt4_gate.py
python tools/governance/run_infinity1_flagship_verification.py
```

| Gate | Result | Notes |
|------|--------|-------|
| genome-gate | **PASS** | 178 genome(s) valid |
| naming-gate | **PASS** | 163 grandfathered legacy paths, 0 warning(s) |
| alt4-gate | **PASS** | 178 genome(s) valid; 0 pending promotion(s) |
| infinity1-flagship-verification | **PASS** | 13/13 steps (includes operator-workflow-runtime-gate) |

**Outcome:** Wave 5 closure **complete** — no lineage or naming patches required on this workspace. Stale failures in the 2026-06-06 flagship audit table are superseded by this rerun.

## Planned fixes (if gates regress)

### genome-gate lineage symmetry

| Parent | Expected children | File |
|--------|-------------------|------|
| `coding_organs_stack` | `patchforge_organ`, `change_scope_organ` | `governance/subsystem_genomes/coding_organs_stack.genome.v1.json` |
| `aris_integration_organ` | `aris_standalone_service` | `governance/subsystem_genomes/aris_integration_organ.genome.v1.json` + reciprocal parent on standalone service genome |

### naming-gate

Confirm grandfather entries for `movie_renderer_lane_organ`, `story_forge_launcher_organ`, `text_game_to_video_organ` in `governance/legacy_engineering_aliases.v1.json`. Apply MP-X rename only if grandfather path is insufficient.

## Exit criteria

- [x] `genome-gate` PASS
- [x] `naming-gate` PASS
- [x] `alt4-gate` PASS
- [x] `infinity1-flagship-verification` 13/13 PASS
- [x] Sign-off updated: flagship GA **Proven** (see [SEAM_STRESS_OPERATOR_SIGNOFF_2026-06-06.md](./SEAM_STRESS_OPERATOR_SIGNOFF_2026-06-06.md))

## Optional gate

```bash
make seam-stress-gate
```

Offline seam discovery smoke + pytest (see Makefile).
