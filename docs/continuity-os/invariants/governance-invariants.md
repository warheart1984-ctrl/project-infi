# Governance Invariants (CRK-1)

Book of Invariants Section III.

| ID | Invariant |
|----|-----------|
| **G-1** | Every decision must emit a Governance Receipt (GRR-1) |
| **G-2** | Every steward must remain challengeable (KΩ) |
| **G-3** | No steward may self-ratify its own correctness |
| **G-4** | Governance must be invariant to steward identity |

## GRR-1

Answers: **"Why did we think this?"**

Preserves observation → interpretation → valuation → commitment → outcome.

## KΩ

Kernel must remain **consequence-exposed** — challengeable by reality and external stewards.

## Red-team mapping

| Attack class | Invariants tested |
|--------------|-------------------|
| B1 Mechanical | K0–K2 |
| B2 Structural | K3–K6 |
| B3 Semantic | K7–K12 |
| B4 Founder capture | Reproduction independence |

## Spec

[CRK-1 Governance](../architecture/crk1-governance.md) · [Mission #003](../missions/mission-003.md)
