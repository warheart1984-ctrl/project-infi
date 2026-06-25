# Receipts

Constitutional preservation artifacts.

## GRR-1 — Governance Reconstruction Receipt

**Question:** *Why did we think this?*

| Section | Content |
|---------|---------|
| Observation | Evidence refs |
| Interpretation | Hypotheses, selected model |
| Valuation | Values in play |
| Commitment | Chosen action |
| Outcome | Continuity assessment |
| Reflection | Decisive invariants |

Schema: `fixtures/crk1/governance_reconstruction_receipt.schema.json`

## CRR-1 — Calibration Reconstruction Receipt

**Question:** *Why did we stop thinking this?*

| Section | Content |
|---------|---------|
| `prior_judgment_state` | Before correction |
| `reality_contact` | Evidence observed |
| `contradiction` | Expected vs actual, surprise |
| `correction` | Update rule, model shift |
| `calibration_gained` | Delta, new confidence |
| `continuity_linkage` | Invariant implications |
| `integrity` | Hashes, verification |

Schema: `fixtures/crk1/calibration_reconstruction_receipt.schema.json`

Builder: `src/crk1/crr1_builder.py`

## KCR — Kernel Challenge Receipt

Emitted when kernel invariants are challenged via Mission #004 loop.

## D-3 Seal — Reproduction Certificate

External steward attestation for Mission #003.

Module: `src/crk1/d3_reproduction_certificate.py`

## Comparison

| Receipt | Preserves | Continuity role |
|---------|-----------|---------------|
| GRR-1 | Judgment | Decision memory |
| CRR-1 | Corrigibility | **Atomic unit of continuity** |
| KCR | Kernel challenge | KΩ enforcement |
| D-3 | Reproduction | Founder independence |

## Related

[Book of Invariants](../continuity-os/invariants/book-of-invariants.md)
