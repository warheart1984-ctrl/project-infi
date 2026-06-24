# Constitutional Failure Modes

Formal failure taxonomy for the RPA-1 constitutional stack.

## F-1 — Observer Failure (Reality Blindness)

- Observation no longer tracks external reality.
- Synthetic, censored, or fabricated inputs dominate.
- Violates OPA-1 and RPA-1.2.
- **Symptom:** cycles exist, but `observation` is detached from the world.

## F-2 — Judgment Failure (Reality Ignorance)

- Evidence is seen but not allowed to constrain judgment.
- Doctrine, hierarchy, or incentives override contradictory signals.
- Violates JPA-1 and CRK-1.J.
- **Symptom:** outcomes repeatedly contradict expectations with no change in thresholds or policies.

## F-3 — Correction Failure (Reality Disempowerment)

- The system structurally loses the ability to be corrected by reality.
- Reality Vetoes are suppressed, ignored, or never triggered.
- Corrigibility collapses; `corrigibilityStatus` drifts to `"failed"` across lineages.
- Violates RPA-1 directly.
- **Symptom:** cycles, reports, and recalibrations continue, but reality has no veto power.

## Continuity Health States

| State | Condition |
|-------|-----------|
| **healthy** | At least one lineage maintains sound, reality-correctable cycles under RPA-1 |
| **at-risk** | F-1 or F-2 appear locally but vetoes still fire and corrections occur |
| **collapsed** | F-3 holds system-wide: reality can no longer overrule judgment anywhere in the lineage |

## Runtime Detection

`InMemoryContinuityLedger.getContinuityHealth()` computes:

- `failureModes`: detected F-1 / F-2 / F-3 heuristics
- `lineageCorrigibility`: rollup across observer lineages
- `soundLineageCount` / `failedLineageCount`
- `pendingVetoCount`

Use `getFailedLineages()` to query observers whose corrigibility has collapsed.

## Related

- [RPA-1 Whitepaper](./RPA-1-WHITEPAPER.md)
- [Constitutional Stack](./CONSTITUTIONAL-STACK.md)
- [Reality → Continuity Diagram](./REALITY-EVIDENCE-JUDGMENT-STACK.md)
