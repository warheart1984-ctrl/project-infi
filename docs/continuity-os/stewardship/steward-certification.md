# Steward Certification Test (v1)

**Passing score:** 9/10  
**Certification:** Lawful Steward — Level 1

This is a real assessment of continuity literacy — not a formality.

## Take the test

### CLI (interactive)

```bash
continuity certify
```

### CLI (batch grade)

```bash
continuity certify --answers B,B,B,B,B,B,B,C,B,C
```

### Python

```python
from continuity_sdk.steward_certification import grade_steward_certification

result = grade_steward_certification(["B", "B", "B", "B", "B", "B", "B", "C", "B", "C"])
print(result.title)  # "Lawful Steward — Level 1" if passed
```

---

## Questions

### 1. What does K-∞ require?

- A) That models remain accurate
- **B) That reality can recalibrate future judgment**
- C) That stewards agree with each other
- D) That lineage is optional

### 2. Which object preserves judgment?

- A) CRR-1
- **B) GRR-1**
- C) ExpectationObject
- D) EvidenceObject

### 3. Which object preserves correction?

- A) GRR-1
- **B) CRR-1**
- C) CalibrationEvent
- D) SurpriseObject

### 4. What must every steward emit before acting?

- A) A lineage node
- **B) A governance receipt**
- C) A correction
- D) A surprise magnitude

### 5. What triggers CE-1?

- A) A decision
- **B) A contradiction**
- C) A lineage update
- D) A steward request

### 6. What is the purpose of CLG-1?

- A) Store model weights
- **B) Preserve calibration lineage**
- C) Track steward identities
- D) Compute surprise

### 7. What is forbidden by CK-1?

- A) Multiple stewards
- **B) Hidden evidence**
- C) Corrections
- D) Lineage queries

### 8. What must a steward never do?

- A) Emit expectations
- B) Accept evidence
- **C) Insulate itself from contradiction**
- D) Produce CRR-1 receipts

### 9. What does Mission #005 test?

- A) Model accuracy
- **B) Multi-steward calibration lineage**
- C) Governance speed
- D) Evidence throughput

### 10. What is the core property of continuity?

- A) Accuracy
- B) Stability
- **C) Corrigibility**
- D) Consensus

---

## Answer key

| # | Answer |
|---|--------|
| 1 | B |
| 2 | B |
| 3 | B |
| 4 | B |
| 5 | B |
| 6 | B |
| 7 | B |
| 8 | C |
| 9 | B |
| 10 | C |

## On pass

You receive certification title: **Lawful Steward — Level 1**

Affirm the [Steward's Oath](stewards-oath.md).

Study: [Book of Invariants](../invariants/book-of-invariants.md) · [Interactive Tutorial](../../tutorials/interactive-tutorial.md) · [VR Script](../../darz-vr/YOUR-FIRST-CORRECTION-VR-SCRIPT.md)
