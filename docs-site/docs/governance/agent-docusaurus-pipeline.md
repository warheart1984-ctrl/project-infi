# Agent Docusaurus Pipeline

:::info Documentation status
This page declares an **agent-usable documentation loop** for the AAES-OS docs site.
The CLI under `docs-site/scripts/agent-doc-pipeline.mjs` prepares and records the stages below.
It does **not** by itself prove that every documentation claim matches runtime behavior — only the checks it runs and stores in the receipt.
:::

## Goal

Make Docusaurus usable by **any** coding agent (Cursor, Claude Code, Codex, Jules, etc.) through one shared loop:

```text
Agent action
  ↓
Observed repository diff
  ↓
Test and runtime evidence
  ↓
Generated documentation
  ↓
Conformance check
  ↓
Signed record
```

Agents do not need a special Docusaurus MCP.
They need:

1. Markdown under `docs-site/docs/`
2. A sidebar entry in `docs-site/sidebars.js`
3. The pipeline CLI (or equivalent manual stages)
4. Evidence-bound wording (Drive-G-1)

## Stage map

| Stage | What the agent does | What the pipeline records |
| --- | --- | --- |
| 1. Agent action | Edit code / docs; name the action | `--action`, `--agent` |
| 2. Observed repository diff | Prefer `git status` / `git diff` scoped to `docs-site` | porcelain + diff stats + HEAD |
| 3. Test and runtime evidence | Run docs verify when docs changed | `build-docs-site` + `smoke-docs-site` |
| 4. Generated documentation | Add/update `.md` pages; keep claims evidence-bound | docs paths + required page presence |
| 5. Conformance check | Ensure every sidebar id has a page; smoke passes | missing page list + verify result |
| 6. Signed record | Optional `DOC_PIPELINE_SIGNING_KEY` | SHA-256 envelope hash + Ed25519 signature or `unsigned` |

## Commands

From `docs-site/`:

```bash
# Full loop after a docs change
npm run agent:pipeline -- --action "add-constitutional-gravity" --agent cursor

# Hash-bound record without rebuild (faster iteration)
npm run agent:pipeline -- --action "draft-only" --skip-verify

# Inspect shape without writing a receipt
npm run agent:pipeline -- --dry-run --skip-verify
```

Receipts write to:

- `docs-site/receipts/agent-doc/agent-doc-<timestamp>.json`
- `docs-site/receipts/agent-doc/latest.json`

### Optional signing

```bash
# Ed25519 private key PEM
export DOC_PIPELINE_SIGNING_KEY="$(cat path/to/ed25519-private.pem)"
npm run agent:pipeline -- --action "release-docs-slice" --agent cursor
```

Without the key, the record remains **hash-bound** with `signing_status: "unsigned"`.
That is still a valid pipeline receipt; it is not a durable cryptographic attestation.

## Rules for any coding agent

1. **Read `docs-site/AGENTS.md` first** when changing documentation.
2. **Prefer the CLI** over inventing a parallel docs process.
3. **Drive-G-1**: do not claim implements / enforces / complete without code, tests, schemas, or receipt evidence.
4. **Sidebar + page pair**: every new page id in `sidebars.js` must have `docs/<id>.md` (or `.mdx`).
5. **Run verify** before treating a docs slice as done (`npm run verify` or the pipeline without `--skip-verify`).
6. **Attach the receipt path** in PR / handoff notes when a signed or hash-bound record exists.

## How this stays agent-agnostic

| Mechanism | Who uses it |
| --- | --- |
| `docs-site/AGENTS.md` | Any agent that reads repo agent guides |
| `.cursor/skills/agent-docusaurus-pipeline/` | Cursor agents |
| `npm run agent:pipeline` | Any agent with a shell |
| Receipt JSON schema (below) | Humans, CI, stewards |

No vendor lock-in: if an agent cannot read Cursor skills, it can still follow `AGENTS.md` and run the CLI.

## Receipt shape (declared)

```json
{
  "artifact": "agent-docusaurus-pipeline-record",
  "version": "0.1.0",
  "status": "pipeline-record",
  "truth_boundary": "…",
  "stages": {
    "1_agent_action": {},
    "2_observed_repository_diff": {},
    "3_test_and_runtime_evidence": {},
    "4_generated_documentation": {},
    "5_conformance_check": {},
    "6_signed_record": {}
  },
  "envelope_hash_sha256": "…",
  "signing": {
    "signing_status": "unsigned|signed"
  }
}
```

## Related

- [Constitutional Release Receipt](./constitutional-release-receipt.md)
- [Constitutional Laws of Intelligence](./constitutional-laws-of-intelligence.md)
- [The Principle of Constitutional Gravity](./constitutional-gravity.md)
