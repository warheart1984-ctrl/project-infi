# Nova Operator Certification — Level 3 (Constitutional Engineering)

**Version:** 1.0  
**Prerequisite:** [Level 2 Certification](./OPERATOR-LEVEL-2-CERTIFICATION.md)  
**Audience:** Operators, architects, and engineers responsible for modifying, extending, or validating CRK-1 itself.

---

## 1. Certification Objectives

A Level 3 Operator must demonstrate mastery in:

- Understanding and modifying CRK-1 constitutional law
- Designing and validating new invariants
- Performing kernel-level audits
- Executing continuity-level forensics
- Debugging ledger inconsistencies
- Running kernel fuzz tests
- Managing multi-agent constitutional drift
- Performing constitutional upgrades without breaking continuity

This is the highest non-founder certification.

---

## 2. Exam Structure

| Section | Content | Items |
|---------|---------|-------|
| A | Constitutional Theory | 15 MCQs |
| B | Kernel Engineering | 10 short answers |
| C | Constitutional Modification | 5 design tasks |
| D | Kernel Forensics | 2 deep-dive investigations |
| E | Live Constitutional Upgrade | 1 practical exam |

**Passing score:** 95%  
**Failure:** 30-day cooldown before retaking.

---

## 3. Section A — Constitutional Theory (Sample Questions)

1. The lawful action predicate is defined as:
   - A. A heuristic
   - B. A soft constraint
   - C. A conjunction of all invariants
   - D. A plan-level suggestion

2. A constitutional upgrade must preserve:
   - A. UI layout
   - B. Continuity hashes
   - C. Operator preferences
   - D. Agent personality

3. The pattern ledger's cryptographic chain ensures:
   - A. Faster execution
   - B. Immutable action history
   - C. Better syntax highlighting
   - D. Automatic refactoring

*(15 total — full question bank maintained by operator certification board.)*

---

## 4. Section B — Kernel Engineering (Sample Questions)

1. Explain how CRK-1 enforces fail-closed behavior.
2. Describe the difference between a kernel panic and an invariant violation.
3. How does lazy T5 binding interact with lineage?
4. What conditions must be met for a constitutional upgrade to be valid?
5. How does PIT-band evolution remain bounded?

*(10 total.)*

---

## 5. Section C — Constitutional Modification Tasks

| Task | Description |
|------|-------------|
| 1 | Design a new invariant that prevents cross-module circular dependencies |
| 2 | Modify the continuity substrate to support snapshot compression |
| 3 | Extend the pattern ledger to include operator annotations |
| 4 | Add a PIT-4 mode for "contextual self-evaluation" |
| 5 | Propose a constitutional amendment to improve replay determinism |

---

## 6. Section D — Kernel Forensics

### Scenario 1 — Ledger Fork at R-00412

- Identify fork origin
- Reconstruct canonical chain
- Repair continuity

### Scenario 2 — Snapshot Drift Across Agents

- Compare continuity hashes
- Identify divergence
- Restore cluster consistency

---

## 7. Section E — Live Constitutional Upgrade

Operator must:

1. Freeze all agents
2. Apply constitutional patch
3. Validate invariants
4. Validate ledger
5. Validate continuity
6. Restart kernel
7. Resume agents
8. Prove continuity preservation

This is the final exam.

---

## Related

- [CRK-1 Kernel Fuzz Harness](../integrity/CRK-1-KERNEL-FUZZ-HARNESS.md)
- [CRK-1 Reference Implementation](../integrity/CRK-1-KERNEL-REFERENCE-IMPLEMENTATION.md)
- [Flight Deck React Spec](./NOVA-FLIGHT-DECK-REACT.md)
