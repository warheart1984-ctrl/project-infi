# CRK-1 Mission Map (M3–M5)

## Mission #003 — Reproduction & Governance

**Seal:** D-3  
**Question:** Can a non-founder rebuild CRK-1 from the packet?

Artifacts: objects, contracts, invariants, drift envelopes, governance receipts, reproduction certificates.

Modules: `mission_003_packet.py`, `reproduction_certifier.py`, `d3_reproduction_certificate.py`, `governance_receipt_header.py`

---

## Mission #004 — Invariant Discovery & Kernel Challenge

**Question:** Are K0–K_n still adequate with respect to reality?

| Concept | Implementation |
|---------|----------------|
| Kernel compliance | receipts + governance engine (K satisfied as implemented) |
| Kernel validity | consequence exposure over time (K still adequate?) |
| `InvariantPerformanceRecord` | `kernel_challenge_loop.py` |
| `KernelChallengeReceipt` (KCR) | `kernel_challenge_loop.py` |
| `InvariantDiscoveryContract` (IDC) | `invariant_discovery_contract.py` |
| KΩ meta-invariant | `docs/crk1/crk1_invariants.yaml` |

See [MISSION-004-KERNEL-CHALLENGE.md](./mission-004/MISSION-004-KERNEL-CHALLENGE.md).

---

## Mission #005 — Reconstruction & Reality Contact

**Seal:** R-3  
**Question:** Can a non-founder reconstruct *why* CRK-1 looks the way it does?

| Concept | Implementation |
|---------|----------------|
| Reproduction vs reconstruction | D-3 rebuilds machine; R-3 rebuilds judgment |
| `ReconstructionTrace` (v1) | `reconstruction_trace.py` |
| `GovernanceReconstructionReceipt` (GRR) | `governance_reconstruction_receipt.py` |
| Consequence vs reality exposure | CE (K0–K12) vs RCL (K13–K15) |
| `RealitySurfaceRegistry` + RDI | `reality_contact_layer.py` |
| R-3 certifier | `reconstruction_certifier.py` |

See [MISSION-005-RECONSTRUCTION-REALITY-CONTACT.md](./mission-005/MISSION-005-RECONSTRUCTION-REALITY-CONTACT.md).

---

## Constitutional completeness

CRK-1 is complete when every layer — including the kernel — is:

1. **Reconstructable** (GRR + traces + operator R)
2. **Reality-contacted** (K13–K15, RDI)
3. **Consequence-exposed** (K0–K12, CE/SE, KCL/IDC, KΩ)

Nothing is beyond review: not judgments, not governance, not the laws that define "unconstitutional."
