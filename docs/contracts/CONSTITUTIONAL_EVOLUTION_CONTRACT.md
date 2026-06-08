# Constitutional Evolution Contract

Status: **active contract** (Mythic Stage 17 / Anatomical Layer 19 / Release 47)

## Purpose

Governed **charter amendment proposals** under Tier-5 maturity tags — proposal-only, dual gate, ledger receipts, no autonomous rewrite.

## Coordination classes

| Class | Meaning |
|-------|---------|
| CEV-0 | Observe charter drift vs tier-5 invariants |
| CEV-1 | Amendment proposal |
| CEV-2 | Adopted amendment (operator + Jarvis; amends charter overlay, preserves charter_id) |
| CEV-3 | Amendment-influenced contextual gate elevation |

## APIs

- `GET /api/operator/constitutional-evolution`
- `POST /api/operator/constitutional-evolution/observe`
- `GET /api/operator/constitutional-evolution/amendments`
- `POST /api/operator/constitutional-evolution/amendments/adopt`

## Verification

```bash
make constitutional-evolution-body-gate
```
