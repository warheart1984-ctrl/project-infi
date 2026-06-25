# Nova Operator Certification — Level 4 (Constitutional Architect)

**Version:** 1.0  
**Prerequisite:** [Level 3 Certification](./OPERATOR-LEVEL-3-CERTIFICATION.md)  
**Audience:** Constitutional engineers responsible for modifying, extending, validating, and evolving CRK-1 itself.

---

## 1. Certification Objectives

A Level 4 Constitutional Architect must demonstrate mastery in:

- Designing and evolving constitutional law (CRK-1)
- Engineering new invariants at the kernel level
- Modifying the lawful action predicate
- Extending the continuity substrate
- Extending PIT-band evolution rules
- Designing new governance objects
- Performing constitutional migrations without breaking continuity
- Running full kernel integrity and fuzz-testing suites
- Designing multi-agent constitutional protocols
- Ensuring cross-agent constitutional coherence

Level 4 operators are effectively constitutional maintainers.

---

## 2. Exam Structure

| Section | Content | Items |
|---------|---------|-------|
| A | Constitutional Theory | 20 MCQs |
| B | Kernel Architecture | 10 short answers |
| C | Constitutional Design | 5 design tasks |
| D | Kernel Forensics | 2 deep-dive investigations |
| E | Constitutional Migration | 1 live exam |
| F | Multi-Agent Constitutional Protocols | 1 simulation |

**Passing score:** 98%

---

## 3. Section A — Sample Questions

1. The lawful action predicate must be: Deterministic, Total, Side-effect free, Purely functional. Which are required?
   - A. 1 & 2
   - B. 1, 2 & 3
   - C. 1, 2 & 4
   - D. All of the above

2. A constitutional amendment must preserve: Continuity, Ledger integrity, Invariant semantics, PIT-band monotonicity. Which are mandatory?

*(20 total.)*

---

## 4. Section B — Kernel Architecture (Sample)

1. Explain how CRK-1 enforces constitutional determinism across agents.
2. Describe the role of the LawContextResolver in PIT-band evolution.
3. How does the kernel guarantee replay determinism?
4. What is the difference between a constitutional amendment and a runtime patch?
5. How does the kernel detect cross-agent constitutional drift?

---

## 5. Section C — Constitutional Design Tasks

| Task | Description |
|------|-------------|
| 1 | Design a new constitutional object type: `ConstraintObject` |
| 2 | Extend the lawful action predicate to incorporate cross-agent consensus |
| 3 | Define a PIT-5 band for "constitutional self-reflection" |
| 4 | Design a new continuity proof format that includes operator annotations |
| 5 | Propose a constitutional amendment that improves multi-agent replay determinism |

---

## 6. Section D — Kernel Forensics

**Scenario 1 — Constitutional Drift Across 4 Agents:** identify drift origin, reconstruct canonical state, restore cluster coherence.

**Scenario 2 — Ledger Fork + Continuity Divergence:** forensic reconstruction, chain integrity, continuity repair.

---

## 7. Section E — Live Constitutional Migration

Freeze agents → export state → apply amendment → validate invariants, ledger, continuity, PIT transitions → restart kernel → resume agents → prove continuity preservation.

---

## 8. Section F — Multi-Agent Protocol Simulation

Run a 6-agent cluster, introduce controlled drift, restore coherence, validate cross-agent PIT alignment and cluster-wide continuity.

---

## Related

- [CRK-2 Spec](../CRK-2-SPEC.md)
- [CRK-1 → CRK-2 Migration](../CRK-1-TO-CRK-2-MIGRATION-PLAN.md)
- [Control Tower Consensus](./NOVA-CONTROL-TOWER-CONSENSUS.md)
