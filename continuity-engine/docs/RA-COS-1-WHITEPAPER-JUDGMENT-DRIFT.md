# RA-COS-1 — Judgment Drift Trace (RA-COS-1.JD)

## 5. Judgment Drift Trace (RA-COS-1.JD)

RA-COS-1 extends its trace model to include **JudgmentDriftEvents**, enabling future stewards to reconstruct how judgment capability changed over time.

### RA-COS-1.JD.1 — Event Definition

A JudgmentDriftEvent records:

- observerId
- previous judgment capability vector
- current judgment capability vector
- computed drift score
- contributing evidence
- timestamp

### RA-COS-1.JD.2 — Trigger Conditions

A drift event MUST be recorded when:

- drift exceeds a configured threshold
- valuation or deliberation capability drops sharply
- reflection capability stagnates
- commitment patterns diverge from constitutional constraints
- CRK-1 flags a legitimacy concern

### RA-COS-1.JD.3 — Purpose

Judgment drift events allow:

- reconstruction of judgment lineage
- detection of systemic drift
- targeted stewardship interventions
- constitutional audits of judgment legitimacy

### RA-COS-1.JD.4 — Integration

Judgment drift events are consumed by:

- JPSS-2 (training adjustments)
- CSS-2 (threshold governance)
- CRK-1 (legitimacy checks)
- Lineage tools (continuity analysis)

---

## Runtime Support

| API | Module |
|-----|--------|
| `JudgmentDriftEvent` | `ra-cos1/judgment-drift-trace.ts` |
| `detectJudgmentDriftTriggers()` | `ra-cos1/judgment-drift-trace.ts` |
| `recordJudgmentDriftEvent()` | `ra-cos1/judgment-drift-trace.ts` |
| `makeJudgmentDriftTrace()` | `ra-cos1/judgment-drift-trace.ts` |
