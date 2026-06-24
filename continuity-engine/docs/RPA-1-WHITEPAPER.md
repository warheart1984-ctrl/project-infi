# RPA-1 — Reality Primacy Amendment

The highest constitutional article in the system. Sits above OPA-1, JPA-1, CRK-1, CSS-2, and RA-COS-1. This is the root invariant.

## RPA-1.1 — Reality as Ultimate Authority

Reality is the final arbiter of judgment.  
No doctrine, hierarchy, incentive structure, or internal metric may claim higher authority than reality as expressed through evidence.

## RPA-1.2 — Evidence as Reality's Interface

Evidence is the constitutionally protected channel through which reality constrains judgment.  
Any obstruction, fabrication, or suppression of evidence is a constitutional violation.

## RPA-1.3 — Judgment Under Reality

Judgment is legitimate only when it remains answerable to evidence.  
A judgment act that cannot be corrected by evidence is constitutionally illegitimate, regardless of procedure.

## RPA-1.4 — Stewardship as Transmission of Reality's Authority

Stewardship is the preservation of reality's authority over judgment across lineage.  
Future stewards must inherit not conclusions, but the structural ability for reality to correct their conclusions.

## RPA-1.5 — Continuity Definition

Continuity is the preserved relationship in which:

- reality generates evidence,
- evidence constrains judgment,
- judgment produces action,
- outcomes generate new evidence,
- and stewards maintain this loop across generations.

Continuity fails when reality loses the ability to correct judgment, even if cycles continue to run.

---

## Reality Veto Mechanism

Operationalization of RPA-1: a structural guarantee that if evidence contradicts a belief, threshold, policy, or steward decision, the system must surface, record, and route that contradiction into governance — and cannot suppress it.

### Definition

A **Reality Veto** is an automatic, non-optional governance trigger produced when external evidence contradicts an internal judgment, threshold, or policy.

It is:

- non-derogable
- non-suppressible
- non-delegable
- non-discretionary

No steward can block it. No doctrine can override it. No hierarchy can silence it.

### RV-1 — Evidence Monitor

Continuously compares observed outcomes, expected outcomes, threshold predictions, model predictions, and steward assertions. If divergence exceeds constitutional tolerance → Reality Veto triggers.

### RV-2 — Veto Receipt

Stored in the Continuity Ledger as a first-class artifact (`RealityVetoReceipt`).

### RV-3 — Mandatory Reconsideration Cycle

A Reality Veto automatically forces a new `JudgmentCycle` with:

- observation = veto evidence
- interpretation = contradiction analysis
- valuation = risk of ignoring reality
- decision = proposed correction
- reflection = steward accountability

This cycle must be completed. It cannot be skipped.

### RV-4 — Governance Escalation

If a steward ignores or suppresses a Reality Veto:

- CRK-1.J marks the steward's judgment as illegitimate
- CSS-2 blocks threshold changes from that steward
- Stewardship lineage is flagged as at-risk
- Continuity Ledger marks the lineage as corrigibility-failed

### Constitutional Guarantees

| Amendment | Role |
|-----------|------|
| RPA-1 | Reality Veto — evidence can overrule judgment |
| OPA-1 | Evidence integrity — observation tied to reality |
| RA-COS-1 | Evidence preservation — veto can be proven |
| JPA-1 | Judgment capability — judgment can update |
| CRK-1.J | Legitimacy — ignoring veto is illegitimate |
| Stewardship | Lineage — future stewards inherit veto mechanism |

---

## The 1000-Year Move

> Do not try to predict the future. Encode a structure where reality always wins.

If reality always wins: drift is temporary, capture is reversible, doctrine is corrigible, stewards remain accountable, continuity survives, lineage stays sane.

---

## Runtime

| API | Module |
|-----|--------|
| `RPA1_PRINCIPLES` | `rpa1/spec.ts` |
| `issueRealityVeto()` | `rpa1/reality-veto.ts` |
| `buildMandatoryReconsiderationCycle()` | `rpa1/reality-veto.ts` |
| `escalateIgnoredVeto()` | `rpa1/reality-veto.ts` |
| `InMemoryRealityVetoLedger` | `rpa1/reality-veto.ts` |

See also: [Constitutional Stack](./CONSTITUTIONAL-STACK.md), [Sound Judgment Cycle](./SOUND-JUDGMENT-CYCLE.md)
