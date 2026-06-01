# P12 — Lineage Reproducibility Proof

Status: **asserted** (local contract verification; cross-machine RC proof pending Gate F).

Authority: `docs/forge-lineage-contract.md`, `REPO_PROOF_LAW.md`.

## Claim

Two builds with identical reproducibility components (pipeline, seed, git commit, backend, adapter) produce the same `lineage_id` regardless of `build_host`.

## Verification (local)

```bash
python3 wolf-cog-os/scripts/emit-forge-lineage.py \
  --pipeline wolf-cog-os/forge/pipelines/daily-driver.yaml \
  --git-commit deadbeef \
  --build-host host-a \
  --output ci-artifacts/lineage-repro-a.json

python3 wolf-cog-os/scripts/emit-forge-lineage.py \
  --pipeline wolf-cog-os/forge/pipelines/daily-driver.yaml \
  --git-commit deadbeef \
  --build-host host-b \
  --output ci-artifacts/lineage-repro-b.json

python3 wolf-cog-os/scripts/validate-lineage-reproducibility.py \
  --lineage-a ci-artifacts/lineage-repro-a.json \
  --lineage-b ci-artifacts/lineage-repro-b.json \
  --ignore-build-host \
  --mode fail

python3 -m unittest tests.test_lineage_reproducibility
```

## Stable promotion binding

Stable channel promotions require `--expected-lineage-id` via `validate-promotion-source.py`.

## Debt

- Gate F RC artifact with live workflow URLs (prerequisite for production cross-machine proof).
- Byte-identical ISO reproducibility not yet proven.
