# Your First Correction — Animation Beats

Four short animations derived from [Your First Correction VR Script](YOUR-FIRST-CORRECTION-VR-SCRIPT.md). Each can ship as a standalone clip or stitch into a single explainer.

**Total stitched runtime:** ~30–40s (plus title/outro).

---

## 1. Expectation (5–10s)

| Beat | Detail |
|------|--------|
| **Camera** | Close on holographic panel |
| **Panel text** | `Expectation: 1.0s` · `Confidence: 0.8` · `Channel: gravity.local` |
| **Action** | Hand/ray press **Submit** |
| **Payoff** | GRR-1 scroll appears, tethered to steward by line of light |
| **VO** | *"Every steward begins with an expectation."* |
| **End frame** | Scroll label `GRR-1` readable |

**Export tag:** `continuity_beat_expectation`

---

## 2. Contradiction (5–10s)

| Beat | Detail |
|------|--------|
| **Camera** | Slow-motion on falling luminous sphere |
| **Timer** | `Observed: 0.3s` counts up in mid-air |
| **Impact** | Shockwave across chamber floor |
| **Rune** | **Contradiction** ignites (flare → hold) |
| **Vector** | Line between `Expected: 1.0s` and `Observed: 0.3s` |
| **VO** | *"Contradiction detected. Δ = 0.7. Surprise: high."* |
| **End frame** | Δ label at vector midpoint |

**Export tag:** `continuity_beat_contradiction`

---

## 3. Correction (5–10s)

| Beat | Detail |
|------|--------|
| **Camera** | Medium shot on contradiction vector + new hologram |
| **Hologram** | `Correction Vector: +0.7` · `Calibration Delta: 0.7` |
| **Animation** | Delta number counts 0 → 0.7 over 1.5s |
| **Payoff** | CRR-1 leaf grows from steward tether line |
| **VO** | *"Correction computed. A Calibration Reconstruction Receipt — CRR-1 — has been created."* |
| **End frame** | Leaf fully formed, label `CRR-1` |

**Export tag:** `continuity_beat_correction`

---

## 4. Lineage (10–15s)

| Beat | Detail |
|------|--------|
| **Camera** | Pull back from chamber to reveal full CLG-1 tree |
| **Tree** | Trunk = CK-1; branches = CalibrationEvents; leaves = CRR-1 |
| **Highlight** | Player's leaf lights up on steward-labeled branch |
| **Secondary** | Adjacent leaves pulse (inherited calibration) |
| **Text overlay** | **Continuity is preserved.** |
| **VO** | *"Your correction has entered lineage. Future stewards will inherit this calibration."* |
| **End frame** | Wide tree + overlay text |

**Export tag:** `continuity_beat_lineage`

---

## Stitch order

```
[Optional 3s title] → Expectation → Contradiction → Correction → Lineage → [Optional sigil: LAWFUL STEWARD — LEVEL 1]
```

## Technical

- **Aspect:** 16:9 primary; 1:1 and 9:16 crops for social
- **Frame rate:** 30fps minimum; 60fps for slow-mo contradiction beat
- **Audio:** VO + subtle ambient; separate stems for localization
- **Data:** Bind labels from `continuity demo falling-object` JSON output where possible

## Related

- [Full VR Script](YOUR-FIRST-CORRECTION-VR-SCRIPT.md)
- [CLG-1 Lineage](../continuity-os/architecture/clg1-lineage.md)
- [Developer Guide](../continuity-os/developer-guide.md)
