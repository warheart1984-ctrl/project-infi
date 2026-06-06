# URG Cloud Cross-Repo Runbook

Links in-repo federation with external URG cloud platform work.

## Repositories

| Repo | Role |
|------|------|
| `project-infi` | Operator seam, federation grants, trust bundles |
| `wolf-cog-os` | Cluster manifests (`forge/pipelines/ugr-cloud-cluster.yaml`) |
| `Project-Infinity1` | Infinity 1 operator product mirror |

## In-repo verification

```bash
make ugr-cloud-gate
make ugr-platform-gate
make ugr-ingestion-gate
python -m pytest tests/test_ugr_federation_v19_acceptance.py -q
```

## Cross-repo sync checklist

1. Pin manifest version in `docs/URG_CLOUD_PLATFORM.md`.
2. Run bilateral grant scenario (lab guide scenario D).
3. Export trust bundle from `tenant:acme` and verify witness on peer machine.
4. Record mesh-health snapshot in operator console.

## Version pin

Document the external cloud platform commit or release tag beside each bilateral grant issuance.
