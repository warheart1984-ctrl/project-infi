# Codex Handoff Workflow

This document shows the lowest-token way to send a task to Codex and ingest the reply back into your own system.

## Files in the handoff surface

- [codex-handoff-request.schema.json](./codex-handoff-request.schema.json)
- [codex-handoff-reply.schema.json](./codex-handoff-reply.schema.json)
- [CODEX_ROUTER_BRIDGE.md](./CODEX_ROUTER_BRIDGE.md)
- [CODEX_HANDOFF_PACKET.md](./CODEX_HANDOFF_PACKET.md)
- `tools/codex-handoff-cli.ts`
- `tools/codex-handoff-prompt.ts`
- `tools/codex-handoff-ingest.ts`
- `tools/codex-handoff-router.ts`
- `tools/codex-handoff-orchestrator.ts`
- `tools/codex-handoff-smoke.ts`

## Request flow

1. Your system writes a request packet with the exact objective, the current state, the files to touch, and one verification command.
2. Sovereign Router X evaluates the packet and selects the reasoning engine.
3. Your system stores that packet in a stable path, a task ledger, or a queue item.
4. Codex or the selected reasoning engine reads the packet and works only inside the scope the packet defines.
5. If you want the full loop automated, the orchestrator can write the request packet, record the route decision, and ingest the reply in one step.

Example:

```bash
corepack pnpm codex-handoff-prompt "add the next milestone slice" \
  --current-state "release index already points at the handoff packet" \
  --done "release index links" \
  --done "request schema exists" \
  --next-action "add the reply schema and workflow doc" \
  --files "docs/crk1/release/codex-handoff-reply.schema.json" \
  --files "docs/crk1/release/CODEX_WORKFLOW.md" \
  --verification "corepack pnpm codex-handoff validate <packet>" \
  --output .runtime/codex-handoff-request.json
```

Or, when your system already has the reply file, use the orchestrator to write the request and ingest the reply with one command:

```bash
corepack pnpm codex-handoff-orchestrate "add the next milestone slice" \
  --current-state "release index already points at the handoff packet" \
  --done "release index links" \
  --done "request schema exists" \
  --next-action "add the reply schema and workflow doc" \
  --files "docs/crk1/release/codex-handoff-reply.schema.json" \
  --files "docs/crk1/release/CODEX_WORKFLOW.md" \
  --verification "corepack pnpm codex-handoff validate <packet>" \
  --reply .runtime/codex-handoff-reply.json \
  --ledger .runtime/codex-task-ledger.jsonl \
  --request .runtime/codex-handoff-request.json \
  --json
```

## Reply flow

1. Codex writes a reply packet after the work is complete or blocked.
2. Your system ingests the reply, updates its ledger, and decides the next assignment.
3. The reply packet becomes the evidence trail for what changed and what should happen next.

Example:

```bash
corepack pnpm codex-handoff write reply \
  --status done \
  --summary "Added the reply schema, workflow doc, and runnable CLI." \
  --changed-file "docs/crk1/release/codex-handoff-reply.schema.json" \
  --changed-file "docs/crk1/release/CODEX_WORKFLOW.md" \
  --verification "corepack pnpm codex-handoff validate .runtime/codex-handoff-request.json" \
  --next-action "send the next milestone packet" \
  --output .runtime/codex-handoff-reply.json \
  --json
```

## CLI commands

- `corepack pnpm codex-handoff write request`
- `corepack pnpm codex-handoff write reply`
- `corepack pnpm codex-handoff read <file>`
- `corepack pnpm codex-handoff validate <file>`
- `corepack pnpm codex-handoff --json`
- `corepack pnpm codex-handoff-prompt "<prompt>" ...`
- `corepack pnpm codex-handoff-ingest <reply.json>`
- `corepack pnpm codex-handoff-orchestrate "<prompt>" ...`
- `corepack pnpm codex-handoff-smoke`

## Ingestion contract

Your system should treat the packet as the source of truth for the slice:

- `objective` or `summary` tells you what the task was
- `done` or `changed_files` tells you what is already accounted for
- `verification` tells you how the slice was proved
- `next_action` tells you the smallest follow-up step
- `blockers` tells you whether the task can continue
- `selectedModel` tells you which reasoning engine Sovereign Router X chose
- `routeEvaluation` tells you why the orchestration layer made that decision

The ingest script appends a normalized entry into `.runtime/codex-task-ledger.jsonl`.
The smoke script runs the full prompt -> reply -> ingest loop and fails if any stage drifts.

## Why this keeps tokens low

- The packet is small and deterministic.
- Paths replace prose wherever possible.
- One command proves the slice.
- The next step is explicit, so Codex does not need a long back-and-forth.
