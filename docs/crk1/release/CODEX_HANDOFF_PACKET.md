# Codex Handoff Packet

This file is the compact assignment format for handing work to Codex or for routing Codex results back into your own system.

For the formal schemas and the runnable CLI flow, see:

- [codex-handoff-request.schema.json](./codex-handoff-request.schema.json)
- [codex-handoff-reply.schema.json](./codex-handoff-reply.schema.json)
- [CODEX_WORKFLOW.md](./CODEX_WORKFLOW.md)

## When to use it

Use this packet when you want:

- a short, machine-readable task description
- a minimal reply contract
- low-token handoffs between your system and Codex
- a reusable format for repeat milestone work

## Request packet

```json
{
  "objective": "finish docs-site milestone",
  "current_state": "ops-console and scorecard updated",
  "done": [
    "cluster governance",
    "traceability matrix"
  ],
  "next_action": "mirror the new milestone table into docs-site",
  "files": [
    "docs/scorecards/project-infi.md",
    "docs-site/docs/overview.md"
  ],
  "verification": "corepack pnpm --dir docs-site build",
  "blockers": []
}
```

## Reply packet

```json
{
  "status": "done",
  "summary": "Mirrored the milestone table into docs-site.",
  "changed_files": [
    "docs-site/docs/overview.md"
  ],
  "verification": [
    "corepack pnpm --dir docs-site build"
  ],
  "next_action": "update the release index with the same milestone notes"
}
```

## Field guide

| Field | Meaning |
|-------|---------|
| `objective` | The one sentence goal |
| `current_state` | Short state of the world before the task starts |
| `done` | What is already complete and should not be repeated |
| `next_action` | The smallest useful next step |
| `files` | Exact files or paths the task should touch |
| `verification` | The command that proves the slice is real |
| `blockers` | Only include blockers that actually stop progress |

## Integration pattern

1. Your system creates the request packet.
2. Codex uses the packet to stay scoped to the exact slice.
3. Codex returns a reply packet with the changed files, verification, and the next action.
4. Your system stores the reply packet in its task ledger or orchestration log.

## Token-saving rules

- Keep the packet short and concrete.
- Pass paths, not prose, whenever possible.
- Include only one verification command unless you need multiple proofs.
- Use `next_action` to prevent long follow-up explanations.
- Reuse the same packet shape for every milestone.

## Good use cases

- repo cleanup
- milestone handoff
- verification-driven implementation work
- integration task routing
- operator-to-agent assignment

## Not a good fit

- open-ended brainstorming
- high-level architecture debate without a concrete next step
- tasks that need long historical context in the prompt itself
