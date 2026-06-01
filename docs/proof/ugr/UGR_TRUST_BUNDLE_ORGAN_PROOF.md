# UGR Trust Bundle Organ Proof

Claim status: **proven** (cross-profile parity, local organ run) / **asserted** (cross-physical-machine until UGR-D5)

## Claims

| ID | Claim | Status |
|---|---|---|
| TB-1 | Trust bundle organ runs 4 proof scenarios | proven |
| TB-2 | machine-a vs machine-b payload hash parity for deterministic scenarios | proven |
| TB-3 | Hashed proof bundle written to `.runtime/trust-bundles/latest/` | proven |
| TB-4 | Cross-OS CI matrix evidence | asserted (UGR-D5) |

## One-click verification

```bash
make ugr-trust-bundle-gate
python tools/proof/run_ugr_trust_bundle.py --mode fail
```

## Artifacts

| Artifact | Path |
|---|---|
| Organ | `src/ugr/trust_bundle/` |
| CLI | `tools/proof/run_ugr_trust_bundle.py` |
| Doctrine XI bundle | `docs/trust_bundles/2026-05-28-ugr-trust-bundle-organ.md` |
| Contract | `docs/contracts/UGR_TRUST_BUNDLE_ORGAN_CONTRACT.md` |
| Tests | `tests/test_ugr_trust_bundle_organ.py` |
| Generated proof | `.runtime/trust-bundles/latest/proof_bundle.json` |

## Hardware matrix (pending UGR-D5)

| Machine | Role | Outcome | Evidence |
|---|---|---|---|
| local machine-a profile | simulated node A | pass (organ) | proof_bundle.json |
| local machine-b profile | simulated node B | pass (organ) | cross_profile_parity |
| CI ubuntu-latest | pending | asserted | `.github/workflows/ugr-trust-bundle-gate.yml` |
| CI windows-latest | pending | asserted | `.github/workflows/ugr-trust-bundle-gate.yml` |
