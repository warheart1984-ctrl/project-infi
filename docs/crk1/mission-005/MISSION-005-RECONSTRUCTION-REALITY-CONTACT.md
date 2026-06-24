# Mission #005 — Reconstruction & Reality Contact

**Question:** Can a non-founder reconstruct *why* CRK-1 looks the way it does?

## Two layers (reproduction vs reconstruction)

| Layer | Question | Seal | Artifacts |
|-------|----------|------|-----------|
| Reproduction | Can they rebuild the machine? | **D-3** | objects, contracts, invariants, receipts (M3) |
| Reconstruction | Can they rebuild the judgment that built the machine? | **R-3** | GRR, traces, failure lineages, tradeoff records |

## Artifacts

| Artifact | Module | Role |
|----------|--------|------|
| `ReconstructionTrace` (v1) | `reconstruction_trace.py` | Minimal reconstructability log per cycle |
| `GovernanceReconstructionReceipt` (GRR) | `governance_reconstruction_receipt.py` | One judgment cycle — belief, value, tradeoff, reflection |
| `RealitySurfaceRegistry` | `reality_contact_layer.py` | K13 domain registry |
| RDI | `reality_contact_layer.py` | Reality Diversity Index |
| `Mission005ReconstructionCertifier` | `reconstruction_certifier.py` | R-3 Seal certification |

## Reality Contact Layer (K13–K15)

- **K13** — preserve uncontrolled, consequential reality surfaces
- **K14** — RDI must not decrease without GRR
- **K15** — N independent consequence channels (distinct incentives, failures, power)

## Consequence vs reality exposure

- **Consequence exposure (CE)** — consequences can reach judgment (K0–K12)
- **Reality exposure (RCL)** — reality can still generate consequences (K13–K15)

Domestication failure mode: feedback only from curated, low-variance reality.

## R-3 certification levels

1. **R1** — reconstruction trace schema present
2. **R2** — GRR complete for judgment cycles
3. **R3** — operator R reconstructs traces (ŵ_{t+1} ≈ F̂(ŵ_t, ê_t))
4. **R4** — K13–K15 reality contact checks pass
5. **R5** — kernel challenge path configured (KΩ)

## Fixtures

- `fixtures/crk1/reconstruction_trace.schema.json`
- `fixtures/crk1/sample_reconstruction_trace.json`
- `fixtures/crk1/governance_reconstruction_receipt.schema.json`
- `fixtures/crk1/sample_governance_reconstruction_receipt.json`

## Constitutional completeness

CRK-1 is complete not when no more invariants are needed, but when every layer — including the kernel — is **reconstructable**, **reality-contacted**, and **consequence-exposed**.
