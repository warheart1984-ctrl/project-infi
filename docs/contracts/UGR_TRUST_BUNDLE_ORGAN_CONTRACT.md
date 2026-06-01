# UGR Trust Bundle Organ Contract

Authority: `docs/TRUST_BUNDLE_SPEC.md`, `META_ARCHITECT_LAWBOOK.md`

## Scope

The trust bundle organ orchestrates **cross-profile UGR proof** and emits hashed proof bundles:

| Component | Path |
|---|---|
| Organ | `src/ugr/trust_bundle/organ.py` |
| Scenarios | `src/ugr/trust_bundle/scenarios.py` |
| Evidence | `src/ugr/trust_bundle/evidence.py` |
| CLI | `tools/proof/run_ugr_trust_bundle.py` |

## Scenarios (v1)

| ID | Proves |
|---|---|
| `mesh_parity` | Monolith vs distributed deliberation belief parity |
| `causal_rebuild` | Embryo v1 causal graph rebuild + walk |
| `llm_execution_smoke` | Governed LLM execution commit (mock provider) |
| `gate_manifest` | Trust bundle manifest validator passes |

Each scenario runs on **machine-a** and **machine-b** isolated runtime profiles. Cross-profile payload hashes must match for deterministic scenarios.

## Outputs

- `.runtime/trust-bundles/latest/proof_bundle.json`
- `.runtime/trust-bundles/latest/proof_bundle.sha256`

## Verification

```bash
make ugr-trust-bundle-gate
python tools/proof/run_ugr_trust_bundle.py --mode fail
```

Doctrine XI record: `docs/trust_bundles/2026-05-28-ugr-trust-bundle-organ.md`

## Claim boundaries

| Claim | Label |
|---|---|
| Cross-profile deterministic parity (machine-a vs machine-b) | **proven** when organ `overall_status=pass` |
| Cross-OS / cross-physical-machine | **asserted** until CI matrix evidence (UGR-D5) |

## Debt

- **UGR-D5**: Cross-physical-machine / cross-OS Trust Bundle matrix (GitHub Actions ubuntu + windows)
