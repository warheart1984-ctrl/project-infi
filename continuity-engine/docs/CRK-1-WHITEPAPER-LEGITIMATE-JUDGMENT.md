# CRK-1 — Constitutional Category: Legitimate Judgment (CRK-1.J)

## 4. Constitutional Category: Legitimate Judgment (CRK-1.J)

CRK-1 recognizes **legitimate judgment** as a constitutional category upstream of rules, thresholds, and governance procedures.

### CRK-1.J.1 — Definition

Legitimate judgment is the exercise of decision-making that is:

- reality-responsive
- evidence-grounded
- value-aligned
- constitutionally constrained
- reconstructable by future stewards

### CRK-1.J.2 — Requirements

A judgment is legitimate if and only if:

1. **Observation Integrity**  
   It is grounded in reality-responsive observation (OPA-1).

2. **Evidence Traceability**  
   It is supported by a reconstructable evidence trail (RA-COS-1).

3. **Invariant Compliance**  
   It does not violate non-derogable constitutional invariants (CRK-1 core).

4. **Stewardship Accountability**  
   It can be critiqued, revised, or reversed by future stewards without identity loss.

5. **Judgment Capability Preservation**  
   It does not degrade the system's ability to exercise sound judgment in the future (JPA-1).

### CRK-1.J.5 — Corrigibility Requirement

No judgment act is legitimate if it structurally blocks correction by reality.

A judgment cycle is **sound** if:

1. Observation remains connected to external reality (not fully synthetic or censored).
2. Interpretation remains challengeable (alternative framings can be raised and considered).
3. Valuation remains explicit (what matters and why is articulated, not hidden).
4. Commitment remains accountable (an identifiable steward owns the decision and its consequences).
5. Outcomes remain measurable (there are falsifiable signals, not just narrative).
6. Reflection remains behavior-changing (future cycles can actually update).

CRK-1.J declares:

> A judgment act that violates corrigibility on these dimensions is constitutionally illegitimate, even if it passes all internal procedural checks.

Corrigibility is a constitutional condition for legitimacy.

### CRK-1.J.3 — Constitutional Implication

No threshold adoption, Δ-Threshold, governance decision, or recalibration is legitimate unless it satisfies CRK-1.J.

### CRK-1.J.4 — Relationship to OPA-1 and JPA-1

- OPA-1 protects the **inputs** to judgment (observation).
- JPA-1 protects the **capability** of judgment.
- CRK-1.J protects the **legitimacy** of judgment.

Together they form the constitutional triad:

**Observation → Judgment Capability → Legitimate Judgment**

### Failure Hierarchy

| Failure | Meaning |
|---------|---------|
| Observer Failure | Can't see reality |
| Judgment Failure | Can't reason about what matters |
| Correction Failure | Can't be changed by reality |

**Deepest invariant:** Preserve reality-correctable judgment through lineage.

---

## Runtime Support

| API | Module |
|-----|--------|
| `assessLegitimateJudgment()` | `crk1/legitimate-judgment.ts` |
| `CRK1_J_REQUIREMENTS` | `crk1/legitimate-judgment.ts` |
| `assessCorrigibility()` | `judgment/cycle.ts` (CRK-1.J.5) |
| `JudgmentCycleLedger` | `judgment/cycle-ledger.ts` |
| `enforceCRKOnThresholdDelta()` | `crk1/recalibration-guard.ts` |

See also: [Sound Judgment Cycle](./SOUND-JUDGMENT-CYCLE.md)
