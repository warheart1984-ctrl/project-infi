# Cognitive runtime

## StateObjects

- **InsightState** — `insight_id`, `statement`, `source`, `linked_decisions`
- **QuestionState** — `question_id`, `status` (open, resolved), `importance`
- **HypothesisState** — `hypothesis_id`, `statement`, `confidence`, `status`
- **MentalModelState** — `model_id`, `name`, `version`, `scope`, `superseded_by`
- **DecisionPatternState** — `pattern_id`, `description`, `conditions`, `outcomes`

## Receipts

| Type | Kinds |
|------|-------|
| `InsightReceiptV2` | Discovery, Refinement, Invalidation |
| `HypothesisReceiptV2` | Propose, Test, Confirm, Reject |
| `ModelReceiptV2` | Adopt, Update, Retire |
| `CognitiveRemediationReceiptV2` | Closure |

## Invariants

- **CR-1:** No high-impact decision on untested high-uncertainty hypothesis.
- **CR-2:** Superseded mental models linked to replacements.
- **CR-3:** Open core questions visible when making related decisions.

## Remediation

**Trigger:** decision under invalidated model or rejected hypothesis.

**Path:** Identify dependency → Re-evaluate → Update models → Document corrections.
