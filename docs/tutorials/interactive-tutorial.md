# Interactive Tutorial — Your First Correction

A guided narrative through the constitutional calibration cycle.

**VR version:** [Full scene script (Scenes 0–7)](../darz-vr/YOUR-FIRST-CORRECTION-VR-SCRIPT.md) · [Animation beats](../darz-vr/ANIMATION-BEATS.md)

---

## Step 1 — Meet the Kernel

You begin inside the **CK-1 chamber**.  
Six invariants float around you like glowing runes.

A voice says:

> *"These invariants cannot be broken."*

**Invariants visible:** CK-1.1 through CK-1.6 — evidence, contradiction, corrigibility, preservation, lineage, reality.

---

## Step 2 — Emit an Expectation

A panel appears:

```
Expectation: 1.0s
Confidence: 0.8
```

You press **Submit**.  
A **GRR-1** scroll materializes — your governed commitment is on record.

```python
from continuity_sdk import LawfulLLMAdapter, FallingObjectModel

adapter = LawfulLLMAdapter(FallingObjectModel(), steward_id="you")
exp = adapter.predict("Predict fall time for 2m drop.")
```

---

## Step 3 — Reality Arrives

A glowing sphere drops.  
A timer flashes:

```
Observed: 0.3s
```

A shockwave ripples through the chamber.

```python
evidence = adapter.observe({"value": 0.3, "strength": 1.0})
```

---

## Step 4 — Contradiction Detected

The contradiction rune ignites.

```
Δ = 0.7
Surprise: HIGH
```

Reality disagrees. The system **must** show this — CK-1.2.

---

## Step 5 — CE-1 Activates

A correction vector forms:

```
Correction: +0.7
```

A **CRR-1** leaf grows on the lineage tree.

```python
correction, crr1 = adapter.correct(exp, evidence)
print(crr1["crr_id"], crr1["calibration_delta"])
```

---

## Step 6 — Lineage Expands

The **CLG-1** canopy lights up.  
Your correction becomes part of the future.

```bash
continuity console
```

---

## Step 7 — Stewardship Affirmed

A final message appears:

> *"You have preserved continuity.*  
> *You are now a lawful steward."*

```bash
continuity certify
```

---

## What you learned

| Step | Invariant / artifact |
|------|---------------------|
| 1 | CK-1 kernel |
| 2 | GRR-1, ExpectationObject |
| 3 | EvidenceObject, reality channel |
| 4 | Contradiction, Surprise |
| 5 | CE-1, CRR-1 |
| 6 | CLG-1 |
| 7 | Stewardship S-1–S-4 |

## Next

[Steward Certification](../continuity-os/stewardship/steward-certification.md) · [Steward's Oath](../continuity-os/stewardship/stewards-oath.md) · [Developer Guide](../continuity-os/developer-guide.md) · [Mission #005](../continuity-sdk/mission-005.md)
