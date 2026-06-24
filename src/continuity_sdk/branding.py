"""Continuity SDK branding — badge, sigil, and onboarding copy."""

from __future__ import annotations

from pathlib import Path

SDK_BADGE = """\
█████████████████████████████████████████████
█   CONTINUITY SDK — STEWARD INTERFACE v1   █
█   Governed • Corrigible • Lineage‑Safe    █
█   K‑∞  |  CK‑1  |  CRK‑1  |  CE‑1  | CLG‑1 █
█████████████████████████████████████████████"""

SDK_BADGE_SMALL = """\
[ CONTINUITY SDK • v1 ]
Governed • Corrigible • Lineage‑Preserving"""

SDK_SIGIL = """\
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
     REALITY ROOTS"""

SDK_SIGIL_LEGEND = """\
Interpretation:
  ✦ star          — future steward
  upper canopy    — CLG‑1 lineage
  middle trunk    — CK‑1 invariants
  lower roots     — Reality Interface
  symmetry        — continuity"""

STEWARD_ONBOARDING = """\
============================================================
               CONTINUITY SDK — STEWARD ONBOARDING
============================================================

Purpose
-------
The Continuity SDK provides a minimal, constitutional interface
for running governed, corrigible models inside the CRK‑1 / CE‑1 /
CLG‑1 continuity stack. It ensures every steward remains
challengeable, correctable, and lineage‑preserving.

Core Principles
---------------
K‑∞  : Reality must retain the ability to recalibrate judgment.
CK‑1 : Invariants that guarantee corrigibility and continuity.
CRK‑1: Governance of decisions (GRR‑1).
CE‑1 : Calibration pipeline (contradiction → surprise → correction).
CLG‑1: Lineage graph preserving all corrections (CRR‑1).

What the SDK Provides
---------------------
1. LawfulLLMAdapter
   Wraps any model in constitutional governance:
     - ask() → GRR‑1 decision receipt
     - predict() → ExpectationObject
     - observe() → EvidenceObject
     - correct() → CE‑1 → CRR‑1 → CLG‑1

2. run_falling_object_scenario()
   The canonical MVCD demo:
     Expect 1.0s → observe 0.3s → contradiction → correction.

3. run_mission_005_calibration_lineage_stress()
   Multi‑steward calibration lineage test:
     3 stewards → 3 corrections → 3 CRR‑1 receipts → CLG‑1 reconstruction.

Quick Start
-----------
from continuity_sdk import (
    LawfulLLMAdapter,
    FallingObjectModel,
    run_falling_object_scenario,
    run_mission_005_calibration_lineage_stress,
)

# MVCD demo
correction, crr1 = run_falling_object_scenario()
print(crr1["calibration_delta"])

# Mission #005
report = run_mission_005_calibration_lineage_stress()
assert report.passed

Steward Responsibilities
------------------------
- Emit expectations honestly.
- Accept evidence without insulation.
- Allow CE‑1 to compute corrections.
- Preserve CRR‑1 receipts.
- Maintain lineage through CLG‑1.

If you follow these, you are a lawful steward.

============================================================"""


def steward_onboarding_path() -> Path:
    return Path(__file__).resolve().parent / "STEWARD_ONBOARDING.txt"


__all__ = [
    "SDK_BADGE",
    "SDK_BADGE_SMALL",
    "SDK_SIGIL",
    "SDK_SIGIL_LEGEND",
    "STEWARD_ONBOARDING",
    "steward_onboarding_path",
]
