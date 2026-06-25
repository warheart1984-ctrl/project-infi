# CRK-1 Mission Map (M3–M6)

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

Calibration lineage stress (CLG-1 multi-steward): [MISSION-005-CALIBRATION-LINEAGE-STRESS.md](./mission-005/MISSION-005-CALIBRATION-LINEAGE-STRESS.md).

---

## Mission #006 — Continuity via Calibration Assimilation

**Seal:** CAA-1 / CXD-1  
**Question:** Can a steward who never experienced the original contradiction become more calibrated through preserved lineage alone?

| Concept | Implementation |
|---------|----------------|
| Assimilation receipt (CAA-1) | `caa1_assimilation.py` |
| ΔA ≥ τA continuity test | `build_caa1_receipt()`, default τA = 0.15 |
| Isolation proof | `compute_isolation_proof()` |
| Mission runner | `mission_006_calibration_assimilation.py` |
| Prerequisite | Mission #005 lineage + CRR-1 bundle |

See [MISSION-006-CONTINUITY-ASSIMILATION.md](./mission-006/MISSION-006-CONTINUITY-ASSIMILATION.md).

---

## Constitutional completeness

CRK-1 is complete when every layer — including the kernel — is:

1. **Reconstructable** (GRR + traces + operator R)
2. **Reality-contacted** (K13–K15, RDI)
3. **Consequence-exposed** (K0–K12, CE/SE, KCL/IDC, KΩ)
4. **Propagatable** (CAA-1 / CXD-1 assimilation across stewards)

Nothing is beyond review: not judgments, not governance, not the laws that define "unconstitutional."
