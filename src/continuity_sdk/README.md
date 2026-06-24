# Continuity SDK

```
[ CONTINUITY SDK • v1 ]
Governed • Corrigible • Lineage‑Preserving
```

```
█████████████████████████████████████████████
█   CONTINUITY SDK — STEWARD INTERFACE v1   █
█   Governed • Corrigible • Lineage‑Safe    █
█   K‑∞  |  CK‑1  |  CRK‑1  |  CE‑1  | CLG‑1 █
█████████████████████████████████████████████
```

The constitutional interface for lawful stewards and governed models.

## Sigil

```
           ✦
        ╱  │  ╲
      ╱    │    ╲
    ╱     ╱╲     ╲
   │     ╱ │ ╲     │
   │    ╱  │  ╲    │
    ╲  ╱   │   ╲  ╱
      ╲    │    ╱
        ╲  │  ╱
          ╲│╱
          ╱│╲
        ╱  │  ╲
      ╱    │    ╲
     REALITY ROOTS
```

| Layer | Meaning |
|-------|---------|
| ✦ star | Future steward |
| Upper canopy | CLG‑1 lineage |
| Middle trunk | CK‑1 invariants |
| Lower roots | Reality Interface |
| Symmetry | Continuity |

---

```
────────────────────────────────────────────────────────────
                 THE CONTINUITY OS CONSTITUTION
────────────────────────────────────────────────────────────

PREAMBLE
Reality must never lose the ability to recalibrate future
judgment. This is the Prime Directive (K‑∞).

ARTICLE I — THE KERNEL (CK‑1)
The kernel preserves:
  • admissible evidence
  • visible contradiction
  • corrigible judgment
  • preserved correction
  • reconstructible lineage

ARTICLE II — GOVERNANCE (CRK‑1)
All steward actions must emit:
  • Governance Receipts (GRR‑1)
  • Constitutional context
  • Challengeability (KΩ)

ARTICLE III — CALIBRATION (CE‑1)
Contradiction shall produce:
  • Surprise
  • Correction
  • Calibration delta
  • CRR‑1 preservation

ARTICLE IV — LINEAGE (CLG‑1)
All corrections shall enter lineage.
Lineage must remain reconstructible across stewards.

ARTICLE V — STEWARDSHIP
A steward is one who:
  • emits expectations honestly
  • accepts evidence without insulation
  • allows correction without resistance
  • preserves receipts without omission

ARTICLE VI — CONTINUITY
Continuity is the inheritance of future stewards.
It must be preserved.

────────────────────────────────────────────────────────────
```

## Steward onboarding

One-page onboarding sheet: [STEWARD_ONBOARDING.txt](STEWARD_ONBOARDING.txt)

```bash
continuity onboarding
```

## Install

```bash
pip install -e .
continuity info
```

## Quick start

```python
from continuity_sdk import run_falling_object_scenario

correction, crr1 = run_falling_object_scenario()
print(crr1["calibration_delta"])
```

## CLI

```bash
continuity info          # badge + version
continuity onboarding    # steward onboarding sheet
continuity demo falling-object
continuity mission 005
continuity console
```

## Three primitives

| Primitive | Purpose |
|-----------|---------|
| `LawfulLLMAdapter` | Wrap any model in constitutional governance |
| `run_falling_object_scenario()` | Canonical MVCD demo |
| `run_mission_005_calibration_lineage_stress()` | Multi-steward lineage stress test |

## Documentation

- [Continuity OS Whitepaper](../docs/crk1/CONTINUITY_OS_WHITEPAPER.md)
- [Mission #005 — Calibration Lineage Stress](../docs/crk1/mission-005/MISSION-005-CALIBRATION-LINEAGE-STRESS.md)

## Tests

```bash
python -m pytest tests/continuity_sdk/ -v
```
