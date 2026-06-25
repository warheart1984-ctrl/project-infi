"""JPSS-1 and ECK-2 canonical diagrams — formation, reconstruction, stack placement."""

from __future__ import annotations

from constitutional.eck2.spec import ECK2_FORMATION_PIPELINE, ECK2_RECONSTRUCTION_PIPELINE
from constitutional.jpss.spec import JPSS_CANONICAL_CYCLE

JPSS_FORMATION_LOOP_DIAGRAM = """
[Environment]
      ↓
[Perception]
      ↓
[Salience]
      ↓
[Calibration]
      ↓
[Decision]
      ↓
[Outcome]
      ↓
[Reflection]
      ↓
[Calibration Update]
      ↺ (feeds back into future Calibration and implicit Priors)
""".strip()

JPSS_DUAL_PIPELINE_DIAGRAM = """
FORMATION (JPSS-F, forward)
Environment
  ↓
Perception
  ↓
Salience
  ↓
Calibration
  ↓
Decision
  ↓
Outcome
  ↓
Reflection
  ↓
Calibration Update (→ Priors)

RECONSTRUCTION (ECK-R, backward)
Environment
  ↓
Perception Reconstruction
  ↓
Salience Reconstruction
  ↓
Calibration Reconstruction
  ↓
Prior Reconstruction
  ↓
Judgment Reconstruction
  ↓
Significance Reconstruction
  ↓
Continuity Update
""".strip()

JPSS_SAOS_STACK_DIAGRAM = """
[Dark Horse / Strategic Layer]
        ↑
[Immune Runtime / Drift & Failure]
        ↑
[UGR — Constitutional Runtime]
        ↑
[JPSS Judgment Cycle]
(Environment → … → Calibration Update)
        ↑
[Registers: Environment / Salience / Failure / Priors]
        ↑
[Substrate / World]
""".strip()

JPSS_II_THREE_LAYER_STACK_DIAGRAM = """
A. Adaptive Layer (JPSS-A) — What should change
Environment → Perception → Salience → Calibration → Decision → Outcome → Reflection → Calibration Update

B. Invariant Layer (JPSS-I) — What must remain true
Purpose → Core Values → Commitments → Identity → Sacred Constraints

C. Constitutional Layer (JPSS-C) — How the system decides what belongs in A vs B
Invariant Selection → Invariant Elevation → Invariant Revision → Invariant Retirement → Boundary Governance

Note: The adaptive/invariant boundary is itself a judgment (Dar-z insight).
""".strip()


def format_formation_loop_diagram() -> str:
    stages = "\n      ↓\n".join(f"[{stage.replace('_', ' ').title()}]" for stage in JPSS_CANONICAL_CYCLE)
    return f"{stages}\n      ↺ (feeds back into future Calibration and implicit Priors)"


def format_dual_pipeline_diagram() -> str:
    formation = " → ".join(stage.replace("_", " ").title() for stage in ECK2_FORMATION_PIPELINE)
    formation = formation.replace("Calibration Update", "Calibration Update (→ Priors)")
    reconstruction = " → ".join(
        stage.replace("_", " ").title() for stage in ECK2_RECONSTRUCTION_PIPELINE
    )
    return "\n".join(
        [
            "FORMATION (JPSS-F, forward)",
            formation,
            "",
            "RECONSTRUCTION (ECK-R, backward)",
            reconstruction,
        ]
    )


def format_jpss_diagrams() -> str:
    return "\n\n".join(
        [
            "=== JPSS Formation Loop ===",
            JPSS_FORMATION_LOOP_DIAGRAM,
            "",
            "=== Dual Pipeline (Formation vs Reconstruction) ===",
            JPSS_DUAL_PIPELINE_DIAGRAM,
            "",
            "=== JPSS within CK-1 / SAOS Stack ===",
            JPSS_SAOS_STACK_DIAGRAM,
            "",
            "=== JPSS-II Three-Layer Stack (A / I / C) ===",
            JPSS_II_THREE_LAYER_STACK_DIAGRAM,
        ]
    )
