# Proposals

This directory holds governance proposals for this project.

```
proposals/
├── accepted/      — proposals that passed human review and were applied
├── pending/       — proposals awaiting human review
└── executions/    — execution records for each proposal run
```

## Proposal structure

Each proposal is a JSON document:

```json
{
  "id": "proposal-id",
  "status": "pending | accepted | rejected",
  "summary": "One-sentence description of the proposed change",
  "proposedChange": {
    "kind": "feature | fix | guardrail | refactor",
    "target": "path/to/file.ts",
    "rationale": "Why this change is being proposed",
    "diffPreview": "--- a/file\n+++ b/file\n..."
  },
  "governanceCheck": {
    "requiresHumanPromotion": true,
    "applyableDiff": true,
    "changeLineCount": 12,
    "mutationRisk": "low | medium",
    "legibility": "clear | review",
    "notes": []
  },
  "decidedAt": null,
  "decidedBy": null
}
```

## Rules

- `requiresHumanPromotion` is always `true` — there is no auto-apply path
- Proposals with `mutationRisk: "medium"` (guardrail changes or >4 lines) require closer review
- Proposals with `legibility: "review"` (rationale >480 chars or change >6 lines) should be read carefully before acceptance
- Execution records are stored in `executions/` — they are logs, not approvals

## Journaling

When a proposal is applied, the application is recorded in `.local/proposal-apply-journal.md`:
- Which proposal was applied
- Who promoted it
- When it was applied
- What patch was used
