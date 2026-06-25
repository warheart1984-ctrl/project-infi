# Architecture Stabilization Checklist

What must be frozen before the AAES-OS network activates.

## Category 1 — Constitutional Invariants

- [ ] K-∞ Axiom Set — [K_INFINITY_DERIVATION_SKETCH.md](../../crk1/axioms/K_INFINITY_DERIVATION_SKETCH.md)
- [ ] CRC-1 through CRC-7 — [CRC-V0.1-CANONICAL-RUNTIME-CONTRACT.md](../../crk1/CRC-V0.1-CANONICAL-RUNTIME-CONTRACT.md)
- [ ] Governance veto rules — [MULTI_STEWARD_GOVERNANCE_CHARTER.md](../../crk1/governance/MULTI_STEWARD_GOVERNANCE_CHARTER.md)
- [ ] Admissibility criteria
- [ ] Legitimacy criteria

## Category 2 — Runtime Kernel (CRK-1)

- [x] Reconstruction semantics — [CRK1_FORMAL_SEMANTICS.md](../../crk1/runtime/CRK1_FORMAL_SEMANTICS.md)
- [x] Calibration semantics — CRR-1 / `src/crk1/`
- [x] Lineage semantics — CLG-1 / Mission #005
- [x] Continuity semantics — CAA-1 / CDP-1
- [x] Proof algebra (P₁–P₄) — [CRK1_PROOF_ALGEBRA.md](../../crk1/runtime/CRK1_PROOF_ALGEBRA.md)
- [x] Deterministic execution model — [CRK1_STATE_MACHINE.txt](../../crk1/runtime/CRK1_STATE_MACHINE.txt)

## Category 3 — Continuity Demonstration Protocol (CDP-1)

- [x] Hypothesis — [CDP1_CONSTITUTIONAL_SPEC.md](../../crk1/continuity/CDP1_CONSTITUTIONAL_SPEC.md)
- [ ] Control groups
- [ ] Experimental groups
- [x] Judgment metric — [CPM.md](../../crk1/metrics/CPM.md)
- [x] ΔA metric — CPM / assimilation delta
- [x] τA threshold — [TA_SPEC.md](../../crk1/standards/TA_SPEC.md)
- [x] Failure criteria — [cdp1_adversarial_suite.md](../../../sdk/continuity-sdk/experiments/failure/cdp1_adversarial_suite.md)
- [x] Replication requirements — [CDP1_REPRODUCIBILITY_STANDARD.md](../../crk1/standards/CDP1_REPRODUCIBILITY_STANDARD.md)
- [x] Reference Experiment (Mission #006 baseline) — `tests/mission006/`

## Category 4 — Reference Lineage

- [x] Canonical CRR-1 — Mission #005 / `fixtures/crk1/`
- [x] Canonical CLG-1 — `CalibrationLineageGraphCLG1`
- [x] Canonical contradiction class — `physics.fall_time`
- [ ] Canonical task set (expanded beyond fall-time demo)

## Category 5 — Activation Conditions

The network activates when:

- [ ] CRK-1 is frozen
- [ ] CDP-1 Reference Experiment is reproducible
- [ ] K-∞ is ratified
- [ ] Governance Council is seated — [FIRST_WAVE_GOVERNANCE_COUNCIL.md](../governance/FIRST_WAVE_GOVERNANCE_COUNCIL.md)
- [ ] First multi-steward replication succeeds — [CDP1_MULTI_STEWARD_PROTOCOL.md](../../crk1/mission-006/CDP1_MULTI_STEWARD_PROTOCOL.md)

**At that moment, AAES-OS stops being a proposal and becomes a constitutional substrate.**

## Related

- [AAES_OS_NETWORK_GRAPH.md](../governance/AAES_OS_NETWORK_GRAPH.md)
- [GENESIS-PROTOCOL-v1.3.md](../../crk1/GENESIS-PROTOCOL-v1.3.md)
