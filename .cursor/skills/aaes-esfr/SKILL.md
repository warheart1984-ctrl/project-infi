---
name: aaes-esfr
description: >-
  AAES ESFR ship gate. Use for scorecard honesty, PromotionEligibility, and
  Drive-G-2 dimension checks before claiming readiness.
---

# AAES ESFR (PromotionEligibility)

Pipeline slot **last** — not one of the six pre-ESFR roles.

## Checks

1. Evidence exists for each claim (Drive-G-1)
2. Maturity rated by dimension + audience (Drive-G-2) — never one adjective
3. Scorecard: `docs/scorecards/project-infi.md`
4. Separate operator freeze vs commercial / independently reproduced ops

## Outcomes

| Result | Meaning |
|--------|---------|
| `pass` | Named claim boundary is evidenced |
| `hold` | Structure exists but live/reproduction evidence missing |
| `fail` | Claims exceed evidence or tests red |

Preferred vendor skills: `verification-before-completion`, `review-and-ship`, `verify-this`.
