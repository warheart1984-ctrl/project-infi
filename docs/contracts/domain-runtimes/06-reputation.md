# Reputation runtime

## StateObjects

- **ReputationAssetState** — `asset_id`, `type` (project, talk, article, reference), `impact`
- **PublicStatementState** — `statement_id`, `channel`, `topic`, `alignment_with_invariants`
- **ReferenceState** — `reference_id`, `source`, `strength`
- **ReputationProfileState** — `profile_id`, `domains`, `credibility_scores`

## Receipts

| Type | Kinds |
|------|-------|
| `ReputationEventReceiptV2` | Mention, Endorsement, Critique, MisalignmentFlag |
| `StatementReceiptV2` | Publish, Retract, Clarify |
| `ReputationRemediationReceiptV2` | Closure |

## Invariants

- **RRp-1:** No public statement contradicting core constitutional invariants without Clarify or Retract.
- **RRp-2:** Reputation claims backed by verifiable assets or references.
- **RRp-3:** Misalignment flags trigger review.

## Remediation

**Trigger:** misalignment flags, critiques, reputation shocks.

**Path:** Review → Clarify/retract → Engage critic → Update profile.
