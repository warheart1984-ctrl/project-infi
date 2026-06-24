# JPSS-2 — Judgment Capability Curriculum (JPSS-2.J)

## 3. Judgment Capability Curriculum (JPSS-2.J)

JPSS-2 expands its mandate to train the full judgment capability stack defined in JPA-1:

1. **Perception** — noticing anomalies, contradictions, absences
2. **Interpretation** — forming coherent patterns
3. **Valuation** — deciding what matters
4. **Deliberation** — weighing trade-offs and risks
5. **Commitment** — selecting actions under uncertainty
6. **Reflection** — revising judgments in light of new evidence

### JPSS-2.J.1 — Capability Modules

Each capability receives a dedicated module:

- *Perception 201* — anomaly literacy
- *Interpretation 202* — pattern formation
- *Valuation 203* — prioritization and moral weight
- *Deliberation 204* — trade-off reasoning
- *Commitment 205* — threshold formation
- *Reflection 206* — recalibration discipline

### JPSS-2.J.2 — Development Pipeline

The observer lifecycle now maps directly to judgment capability:

- **Observer** — perception + interpretation
- **Senior Observer** — valuation + hypothesis formation
- **Steward** — deliberation + commitment + reflection

### JPSS-2.J.3 — Judgment Capability Ledger

JPSS-2 maintains a capability ledger for each observer:

- capability scores
- drift indicators
- training history
- stewardship readiness

This ledger is consumed by CSS-2 and CRK-1 during governance.

---

## Runtime Support

| API | Module |
|-----|--------|
| `JPSS2_JUDGMENT_CURRICULUM` | `jpss2/judgment-curriculum.ts` |
| `applyJudgmentCurriculumModule()` | `jpss2/judgment-curriculum.ts` |
| `JudgmentCapabilityLedger` | `jpss2/capability-ledger.ts` |
| `updateCapabilityLedger()` | `jpss2/capability-ledger.ts` |
