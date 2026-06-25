# Your First Correction — Full VR Script

**Experience:** DARZ-VR / Continuity OS onboarding  
**Duration:** ~3–4 minutes (single take) or four standalone clips (see [Animation Beats](ANIMATION-BEATS.md))  
**Scenario:** MVCD — falling object (expectation 1.0s, observed 0.3s)  
**Certification outcome:** Lawful Steward — Level 1

---

## Scene 0 — Title

**Environment:** Black space. No geometry. No UI.

**Visual:** A single horizontal line of light fades in at eye level. Text resolves along the line:

```
Continuity OS — Your First Correction
```

**Audio:** Low ambient hum. No voice-over yet.

**Duration:** 3s hold → fade to Scene 1.

---

## Scene 1 — The Kernel Chamber (CK-1)

**Environment:** Vast dim chamber. Floor is matte obsidian; ceiling lost in darkness. Player stands at center.

**Visual:** Six glowing runes orbit the player at chest height, slow counter-clockwise drift. Each rune is labeled:

| Rune | Label |
|------|-------|
| 1 | Evidence |
| 2 | Contradiction |
| 3 | Corrigibility |
| 4 | Correction |
| 5 | Lineage |
| 6 | Reality Channels |

Runes pulse softly at 0.5 Hz. No interaction yet.

**VO (calm, precise):**

> *"This is the Continuity Kernel — CK-1. These invariants cannot be broken."*

**Interaction:** Look-at highlights each rune; optional tooltip shows CK-1.1–CK-1.6 mapping.

**Duration:** 8–12s or until player steps forward (trigger zone).

---

## Scene 2 — Emitting an Expectation

**Environment:** Same chamber. Rune orbit slows and dims to 30%.

**Visual:** Holographic panel materializes 1.2m in front of player:

```
Expectation: 1.0s
Confidence: 0.8
Channel: gravity.local
```

Submit button glows at panel base.

**VO:**

> *"Every steward begins with an expectation."*

**Interaction:** Player reaches out (ray or hand) and presses **Submit**.

**On submit:**

- Panel dissolves into particles.
- A glowing scroll (**GRR-1**) appears at the player's right hand, tethered by a thin line of light to the steward sigil (not yet visible).
- Scroll label: `GRR-1` · steward session ID.

**Wire object (for Unity/API binding):** `GovernanceReceiptHeader` linked to expectation emission.

**Duration:** 10–15s.

---

## Scene 3 — Reality Arrives

**Environment:** Chamber ceiling opens to starfield. A luminous sphere spawns 4m above player.

**Visual:**

- Countdown floats above sphere: **Drop in 3… 2… 1…**
- Sphere falls with physically plausible motion (not necessarily 1.0s — observed time is the lesson).
- Mid-air timer appears beside the fall path:

```
Observed: 0.3s
```

**On impact:** Subtle shockwave ripples through chamber floor and rune ring. Runes flicker once.

**Audio:** Soft impact thud + low-frequency ripple.

**Wire object:** `EvidenceObject` · channel `gravity.local` · `observed_outcome: 0.3`.

**Duration:** 6–8s.

---

## Scene 4 — Contradiction & Surprise (CE-1 F1–F2)

**Environment:** Chamber returns to full interior. Lighting shifts cool blue at contradiction vector.

**Visual:**

- Rune **Contradiction** flares bright white, then holds at 100%.
- Vector line draws between two floating labels:

```
Expected: 1.0s          Observed: 0.3s
```

- Δ label animates at vector midpoint: **Δ = 0.7**
- Surprise meter (optional HUD): **Surprise: high**

**VO:**

> *"Contradiction detected. Δ = 0.7. Surprise: high."*

**Wire objects:** `ContradictionObject`, `SurpriseObject` (CE-1 F1–F2).

**Duration:** 8–10s.

---

## Scene 5 — Correction (CE-1 F3–F5)

**Environment:** Warm amber accent on correction hologram.

**Visual:** New hologram beside the contradiction vector:

```
Correction Vector: +0.7
Calibration Delta: 0.7
```

A **leaf of light** (**CRR-1**) grows from the tether line connecting player to the impact event. Leaf unfurls over 2s; label: `CRR-1`.

**VO:**

> *"Correction computed. A Calibration Reconstruction Receipt — CRR-1 — has been created."*

**Wire objects:** `CorrectionObject`, `CorrectionDeltaObject`, CRR-1 flat dict via `build_crr1()`.

**Duration:** 8–10s.

---

## Scene 6 — Lineage (CLG-1)

**Environment:** Chamber walls dissolve. Camera may auto-pull-back or player floats upward.

**Visual:** Vast **tree of light** fills the void:

| Part | Represents |
|------|------------|
| **Trunk** | CK-1 |
| **Branches** | `CalibrationEvent` nodes |
| **Leaves** | CRR-1 receipts |
| **Roots** | Reality channels (`gravity.local`, …) |

Player's new leaf lights up on a branch labeled with **steward ID**. Nearby leaves (prior stewards) pulse once in acknowledgment.

**VO:**

> *"Your correction has entered lineage. Future stewards will inherit this calibration."*

**Wire object:** `CLG1Ingestion.ingest_crr1()` → `CalibrationEvent` node + edges to Steward, Expectation, Evidence.

**Duration:** 12–18s.

---

## Scene 7 — Stewardship

**Environment:** Tree soft-focus in background. Sigil centers in front of player.

**Visual:** Sigil materializes:

```
LAWFUL STEWARD — LEVEL 1
```

Optional: link to [Steward Certification](../continuity-os/stewardship/steward-certification.md) and [Steward's Oath](../continuity-os/stewardship/stewards-oath.md).

**VO:**

> *"You have allowed reality to correct you. You have preserved the correction. You have extended continuity. You are now a lawful steward."*

**Fade:** Tree remains glowing. Title line from Scene 0 may reappear: *Continuity is preserved.* → black.

**Duration:** 8–10s.

---

## Production notes

| Item | Guidance |
|------|----------|
| **Data binding** | Drive scroll, leaf, and vector labels from live `continuity demo falling-object` or Continuity API — renderer only, no mock IDs |
| **Steward ID** | Use session UUID; persist for CLG-1 branch label |
| **Accessibility** | Full VO + subtitles; reduce motion option disables shockwave |
| **Export** | See [Animation Beats](ANIMATION-BEATS.md) for four standalone clips |

## Related

- [Animation Beats](ANIMATION-BEATS.md) — short clip breakdown
- [Interactive Tutorial](../tutorials/interactive-tutorial.md) — same narrative with code
- [MVCD Demo](../continuity-sdk/mvcd-demo.md) — Python reference
- [Unity Blueprint](DARZ-VR-v0.1-unity-blueprint.md) — prefab and scene setup
