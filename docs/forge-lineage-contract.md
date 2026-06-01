# Forge Reproducible Lineage Contract (P7)

Status: canonical lineage artifact contract for Forge variant pipelines.

Authority: `docs/forge-platform-program.md`.

## Purpose

Every Forge build that promotes through RC/stable channels carries a **forge-lineage.json** artifact describing deterministic build identity.

## Artifact path

- Default: `ci-artifacts/forge-lineage.json`
- Schema: `forge-lineage.v1`

## Key fields

| Field | Role |
|---|---|
| `lineage_id` | SHA256 of canonical component JSON |
| `pipeline_name` | Pipeline spec name |
| `variant_id` | Variant id from pipeline |
| `profile_id` | Forge profile used |
| `substrate_id` | Substrate class/id |
| `rootfs_backend` | Rootfs bootstrap backend |
| `replay_adapter` | Substrate replay layout adapter |
| `package_sets` | Sorted package profile ids |
| `reproducibility_seed` | Pipeline reproducibility seed |
| `parent_lineage_id` | Optional parent lineage hash |
| `git_commit` | Short git commit at emit time (hashed) |
| `build_host` | Host fingerprint (provenance only, not hashed) |

## Emit

```bash
python3 wolf-cog-os/scripts/emit-forge-lineage.py \
  --pipeline wolf-cog-os/forge/pipelines/daily-driver.yaml \
  --profile forge-selfhosted \
  --output ci-artifacts/forge-lineage.json
```

## Validate

```bash
python3 wolf-cog-os/scripts/validate-forge-lineage.py \
  --lineage ci-artifacts/forge-lineage.json \
  --mode fail
```

## Promotion

When `expected_profile_id` is set, `validate-promotion-source.py` requires a valid `forge-lineage.json`.

Stable channel promotions may additionally require `--expected-lineage-id` match.
