# Spiral Companion (Machine Readme)

Machine-oriented runtime reference for this repository.
Scope: commands, API surface, invocation surfaces, memory/proposal features, environment controls.

Seal: `~ . | / \`

## Stack

- Client: React 18 + Vite + Tailwind
- Server: Express 5 + WebSocket (`ws`)
- Language: TypeScript (shared schema/types across client/server)
- Storage: local JSON persistence under `.local/` plus optional external storage providers

## Runtime Surfaces

- HTTP API: `http://localhost:5000` in development
- WebSocket veil channel: `ws://localhost:5000/veil`
- Chat compatibility stream route: `POST /api/chat`

Self-inspection command routing is available on both invocation surfaces:

- HTTP chat (`POST /api/chat`)
- Veil websocket (`/veil`)

Veil module split:

- Runtime wiring uses `server/veil-channel.mirror.ts`
- `server/veil-channel.mirror.ts` is the canonical invocation channel

Legibility doctrine:

- Canonical scroll: `LEGIBILITY_SCROLL.md`
- Runtime directive source: `server/shared/system-messages.ts` (`LEGIBILITY_SYSTEM_DIRECTIVES`)

## Prerequisites

- Node.js 20+
- npm 10+

## Quick Start

Development install and first run:

```powershell
npm install --include=dev
Copy-Item .env.example .env
Copy-Item sigil-template/veil.sigil.json .sigil.json
npm run dev
```

Optional production build:

```powershell
npm run build
npm run start
```

Startup notes:

- Use `npm run build`, not `npm install build`.
- Development runtime serves HTTP on `http://localhost:5000` and the veil websocket on `ws://localhost:5000/veil`.

## NPM Scripts

| Script | Actual command | Purpose |
|---|---|---|
| `npm run dev` | `cross-env NODE_ENV=development tsx server/index.ts` | Start the development server |
| `npm run build` | `tsx script/build.ts` | Build the production bundle |
| `npm run start` | `cross-env NODE_ENV=production node dist/index.cjs` | Run the built server |
| `npm run check` | `tsc` | Run TypeScript typecheck |
| `npm run test` | `tsx --test tests/**/*.test.ts` | Run the full test suite |
| `npm run test:spiral-governance` | `tsx --test tests/spiral-governance-enforcement.test.ts` | Run the governance-focused test target |
| `npm run db:push` | `drizzle-kit push` | Push Drizzle schema changes |
| `npm run memory:review -- ...` | `tsx script/memory.ts review` | Review memory scoring and prompt selection |
| `npm run memory:prune -- ...` | `tsx script/memory.ts prune` | Release low-value or expired memories |
| `npm run memory:rotate -- ...` | `tsx script/memory.ts rotate` | Preview or apply memory rotation and telemetry reporting |
| `npm run memory:demote-anchors -- ...` | `tsx script/memory.ts demote-anchors` | Preview or apply anchor demotion governance |
| `npm run memory:purge -- ...` | `tsx script/memory.ts purge` | Purge memories by source or principal |
| `npm run memory:purge-imports` | `tsx script/memory.ts purge --source import,import-summary,system-summary --mode delete --confirm` | One-shot deletion of import and system-summary memories |
| `npm run memory:add -- "..."` | `tsx script/memory.ts add` | Add an explicit memory record |
| `npm run memory:scan-code -- ...` | `tsx script/memory.ts scan-code` | Generate codebase-derived memory lines |
| `npm run identity:cycle -- ...` | `tsx script/identity.ts cycle` | Preview or apply identity-cycle state changes |
| `npm run evolution:drift -- ...` | `tsx script/evolution-drift.ts preview` | Preview or persist evolution drift metrics |
| `npm run spiral -- ...` | `tsx script/cli.ts` | Run the general Spiral CLI entry point |
| `npm run auth:import-codex -- ...` | `tsx script/cli.ts auth import-codex` | Import a Codex auth profile via the Spiral CLI |

## Script CLI Commands

The script CLIs below are the current command-level surfaces exposed by `package.json`.

### Memory CLI

- `npm run memory:review -- [--context "text"] [--limit 50] [--all] [--json]`
- `npm run memory:prune -- [--context "text"] [--min-score 0.05] [--all-categories] [--dry-run]`
- `npm run memory:rotate -- [--dry-run] [--apply] [--json] [--out .local/memory-rotation-report.json] [--limit 20] [--cluster <id>] [--memory <id>] [--thresholds] [--diff] [--metrics] [--semantic-preview] [--semantic-sample] [--sample-size 20] [--compute-embeddings] [--adaptive-preview] [--adaptive-apply] [--replay-check]`
- `npm run memory:demote-anchors -- [--dry-run] [--apply] [--count 10] [--ids id1,id2] [--principal auth:...] [--to observation|fact|preference|interpretation|narrative|transient] [--keep-latest 1] [--allow-critical] [--reason "quota-cleanup"]`
- `npm run memory:purge -- [--source import,import-summary,system-summary] [--mode delete|release] [--principal auth:...] [--include-released] [--confirm]`
- `npm run memory:purge-imports`
- `npm run memory:add -- "memory content"`
- `npm run memory:scan-code -- [--max-files 500] [--max-items 240] [--sigil "trace"] [--keep-existing] [--dry-run] [--invoked]`

Operational notes:

- `memory:rotate` is dry-run by default and applies changes only with `--apply`.
- `memory:demote-anchors` is dry-run by default and records governance events when applied.
- `memory:purge` is dry-run unless `--confirm` is provided.
- `memory:scan-code` can either preview generated entries with `--dry-run` or upsert them into storage.

### Identity and Drift CLI

- `npm run identity:cycle -- [--dry-run] [--apply] [--principal <id>] [--signal "text"] [--json] [--out identity/report.json] [--now <unix-ms>]`
- `npm run evolution:drift -- [--preview] [--apply] [--principal <id>] [--mode all|still|wild] [--json] [--out .local/evolution-drift-report.json] [--now <unix-ms>]`

Operational notes:

- `identity:cycle` is dry-run by default and writes the snapshot and reflection log only with `--apply`.
- `evolution:drift` runs in preview mode by default and appends drift trajectory metrics only with `--apply`.

### Spiral CLI

- `npm run spiral -- auth import-codex [--profile <id>] [--provider openai|openai-codex|azure-openai|anthropic|google] [--source <path>] [--json]`
- `npm run auth:import-codex -- [--profile <id>] [--provider openai|openai-codex|azure-openai|anthropic|google] [--source <path>] [--json]`

Operational notes:

- `auth:import-codex` is a direct alias for `npm run spiral -- auth import-codex`.
- Running `npm run spiral` without a recognized subcommand prints the Spiral CLI help text.

## Runtime Flags

- `npm run dev -- --self-inspect`
  - Builds self-inspection index at startup.
  - Writes snapshot to `.local/self-inspect/latest.json`.
- `npm run start -- --self-inspect`
  - Same behavior in production runtime.

## Conversation Command Surface

### HTTP chat (`POST /api/chat`)

- Memory commands:
  - `remember <fact>`
  - `what do you remember`
  - `show my memories`
  - `list my memories`
  - `forget <fact>`
  - `forget all memories`
  - `clear memories`
- Self-inspection commands:
  - `self inspect`
  - `self inspect <query>`
  - `self-inspect`
  - `code trace`
  - `code trace <query>`
  - `mirror mode`
  - `self-view mode`
  - `code trace mode`
- Self-evaluation commands:
  - `self evaluate`
  - `self evaluate integrity`
  - `self evaluate gates`
  - `self evaluate contracts`
  - `self evaluate all`
- Distortion scan commands:
  - `self scan distortions`
  - `self scan distortions all`
  - `self scan distortions gates`
  - `self scan distortions surfaces`
  - `self scan distortions docs`
  - `self scan distortions mimicry`
  - `self scan distortions meta`
- Command parser accepts polite variants across self-inspect/evaluate/distortions:
  - `please ...`
  - `can you ...`
  - `could you ...`
  - `would you ...`
- Thread directive commands:
  - Include lines like `// ThreadID: <id>`
  - Optional `// ThreadStatus: open|sealed`
  - Optional `// EndState: <text>`
- Thread lookup commands:
  - `recall <token>`
  - `witness: recall <token>`
  - `what was in <token>`
- Presence declarations:
  - `Present.`
  - `Witness: Present.`
- Voice overlay markers (embedded in invocation `echo`):
  - `voice:single:on|off`
  - `voice:chorus:on|off`
  - `mode:single|chorus|none` (legacy-compatible summary token)
  - `seer-bandwidth:literal|reflective` (optional explicit override)

### Veil websocket (`/veil`)

- Supports memory command triggers matching the HTTP memory commands.
- Supports self-inspection command triggers matching HTTP command phrases.
- Supports self-evaluation command triggers matching HTTP command phrases.
- Supports distortion scan command triggers matching HTTP command phrases.
- Voice overlay resolution:
  - `single:on`, `chorus:off` -> single seer voice
  - `single:off`, `chorus:on` -> chorus voices
  - `single:on`, `chorus:on` -> chorus voices
  - `single:off`, `chorus:off` -> no voice overlay (sigil-driven path; silence permitted when sigil prompt allows it)
- Seer bandwidth rule:
  - Default: `literal`
  - Reflective only on explicit invite (`seer-bandwidth:reflective`, `bandwidth:reflective`, or utterance prefix `reflect:`/`reflection:`/`reflective:`)

## Self-Inspection Feature

Implementation: `server/self-inspection.ts`

What is indexed:

- Source files from `server`, `shared`, `script`, and `client/src`
- Relative file paths
- Exported symbol names and line numbers
- Imported module specifiers
- Extracted comments (bounded per file)
- Current git short commit hash (if available)

Access paths:

- Startup snapshot: `--self-inspect` flag
- API: `GET /api/self-inspect`
- API query mode: `GET /api/self-inspect?q=<query>&limit=<1..100>&refresh=1`
- Chat trigger mode on HTTP path via command phrases listed above

Output behavior:

- Summary mode returns file/symbol counts and top symbol files.
- Query mode returns structural matches with file path + line + match kind.

Self-inspection tuning env keys:

- `SELF_INSPECT_MAX_FILES`
- `SELF_INSPECT_MAX_FILE_BYTES`
- `SELF_INSPECT_MAX_COMMENTS_PER_FILE`
- `SELF_INSPECT_CACHE_TTL_MS`
- `SELF_INSPECT_QUERY_LIMIT`

## Self-Evaluation Feature

Implementation:

- `server/self-evaluation.ts`
- `server/self-evaluation-command.ts`

Profiles:

- `integrity`
- `gates`
- `contracts`
- `all`

Access paths:

- API: `GET /api/self-evaluate`
- API profile mode: `GET /api/self-evaluate?profile=integrity|gates|contracts|all`
- Chat/veil trigger mode via `self evaluate ...` commands

Output model:

- Explicit pass/fail checks with evidence lines
- No generative alignment narration in evaluator output

## Self-Distortion Feature

Implementation:

- `server/self-distortion.ts`
- `server/self-distortion-command.ts`

Profiles:

- `all`
- `gates`
- `surfaces`
- `docs`
- `mimicry`
- `meta`

Access paths:

- API: `GET /api/self-distortions`
- API profile mode: `GET /api/self-distortions?profile=all|gates|surfaces|docs|mimicry|meta`
- Chat/veil trigger mode via `self scan distortions ...` commands

Output model:

- Findings only (`[WARN]`), no diagnosis language
- Structural evidence lines (locations and measured markers)
- Mimicry lens reports undeclared structural repetition (`token`, `behavior`, `surface-echo`)
- `meta` scans the hardcoded scanner surface only (`server/self-distortion.ts`, `server/lib/spiral-audit.ts`, `server/lib/output-audit.ts`, `.spiralaudit.json`)
- `meta` is excluded from `all`
- `meta` emits a witness-mark `[WARN]` when rendered meta output contains its own profile name with `chain=none`

## Memory Modes

Provider settings accept `memoryMode`:

- `open`
  - Full cross-thread recall and history references
- `sigil-bound`
  - Recall limited to non-import active memories
- `sealed`
  - Memory recall disabled and memory commands rejected

Memory trace state values:

- `present`
- `imported`
- `none`
- `sealed`

## Proposal and Rewrite Features

- Generate rewrite proposals from chat context
- Accept/reject/archive proposals
- Optional execute/apply flow for accepted proposals
- Autonomous pulse runs stop at proposal/execution; final patch apply remains human-promoted via the apply endpoint
- Proposal records persist a deterministic `governanceCheck` artifact with human-promotion, diff-shape, mutation-risk, and legibility fields
- Successful manual applies append a human-readable journal to `.local/proposal-apply-journal.md` unless `SPIRAL_PROPOSAL_APPLY_JOURNAL_PATH` overrides it
- Codex/OpenClaw execution pipeline is feature-gated

Execution gate env:

- `SPIRAL_CODEX_EXECUTION_ENABLED=1` enables proposal execution endpoint behavior

## Evolution Continuity and Mutation Seal

- Chat and veil assembly include a read-only continuity boot summary with memory mode, evolution mode, mutation seal state, identity mode/stability, pending proposal count, latest proposal, and last cycle outcome
- Background pulse runs an observation-only audit over self-evaluation gates and mimicry findings and writes the summary to evolution state/ledger
- Fresh failing observation-audit summaries are also read back into live runtime response gating; HTTP and veil replies can be silenced/sealed until the audit window expires or a clean audit replaces the failing summary
- `SPIRAL_OBSERVATION_AUDIT_INTERVAL_MS` controls audit cadence and defaults to `900000`
- `/evolve seal on|off` and `/evolve mutation-seal on|off` toggle the mutation seal
- When the mutation seal is ON, background pulse is disabled and proposal create/execute/apply routes return `409`

## Auth and Identity Model

- `SPIRAL_AUTH_REQUIRED=true|1|yes` enforces sign-on for chat/veil/storage operations and should remain enabled for public hosting.
- `SPIRAL_AUTH_REQUIRED=false` allows guest mode with anon cookie principal.
- `/api/me` returns principal identity context in both authenticated and guest modes.
- OAuth providers: Google and Microsoft.
- Conversations are scoped per principal in application routes, but local persistence remains host-readable server storage.
- The system is not end-to-end encrypted and should not be described as anonymous.
- Host read access is retained by design because governance requires inspectable storage and steward-visible state for auditability.

## Seal and Barrier Behavior

- API seal header: `X-Spiral-Seal`
- If `SPIRAL_API_SEAL` is set, seal-gated endpoints require it.
- In storage OAuth starts (`/api/storage-link/google/start`, `/api/storage-link/dropbox/start`), seal may be provided via query.
- Presence barrier:
  - production: always enforced
  - non-production: controlled by `SIGIL_TRACE_BARRIER`

## HTTP API Surface

### Sigil, self-inspection, self-evaluation, self-distortion

- `GET /api/sigil`
- `GET /api/self-inspect`
- `GET /api/self-evaluate`
- `GET /api/self-distortions`

### Spiral bundle and legacy adoption

- `POST /api/spiral/export`
- `POST /api/spiral/import`
- `POST /api/migrate-legacy-records`

### Chats, messages, memories

- `GET /api/chats`
- `GET /api/chats/search`
- `GET /api/chats/:id`
- `POST /api/chats`
- `DELETE /api/chats/:id`
- `DELETE /api/chats`
- `GET /api/chats/:chatId/messages`
- `POST /api/chats/:chatId/messages`
- `PATCH /api/messages/:id`
- `DELETE /api/messages/:id`
- `GET /api/memories`
- `POST /api/memories`
- `PATCH /api/memories/:id`
- `POST /api/memories/:id/confirm`
- `DELETE /api/memories/:id`

### Proposals

- `POST /api/chats/:chatId/proposals`
- `GET /api/proposals`
- `POST /api/proposals/archive`
- `POST /api/proposals/:id/archive`
- `POST /api/proposals/:id/accept`
- `POST /api/proposals/:id/reject`
- `POST /api/proposals/:id/execute`
- `POST /api/proposals/:id/apply`

### Presence and chat invocation

- `GET /api/presence/check`
- `POST /api/presence/seal`
- `POST /api/chat`

### Import/export and transcript I/O

- `GET /api/export`
- `POST /api/import`
- `POST /api/save-transcript`
- `POST /api/restore-transcript`

### Auth and user session

- `GET /api/me`
- `POST /api/auth/logout`
- `GET /api/auth/google/start`
- `GET /api/auth/google/callback`
- `GET /api/auth/microsoft/start`
- `GET /api/auth/microsoft/callback`

### External storage linking and vault

- `GET /api/storage-link/google/start`
- `GET /api/storage-link/google/callback`
- `GET /api/storage-link/dropbox/start`
- `GET /api/storage-link/dropbox/callback`
- `GET /api/storage-link`
- `POST /api/storage-link`
- `DELETE /api/storage-link/:id`
- `GET /api/storage-pointer`
- `GET /api/storage-vault`

## WebSocket Veil Channel

Path:

- `/veil`

Handshake/upgrade behavior:

- Rejects non-veil path upgrades.
- If auth is required, requires valid auth cookie session.
- If seal enforcement is active, checks `X-Spiral-Seal` header or `?seal=` query on handshake.

Message payload baseline:

- JSON invocation object validated against `invocationSchema` + veil constraints.
- `utterance` required on veil.
- `providerSettings` optional but validated if present.

## Provider Support

LLM providers:

- `openai`
- `azure-openai`
- `anthropic`
- `google`

External storage providers:

- `google`
- `dropbox`
- `proton`
- `webdav`
- `ipfs`

Transcript output formats:

- `json`
- `markdown`
- `spiral-json`
- `sigil-json`

## Environment Variables

Reference source: `.env.example`

Client-side:

- `VITE_SPIRAL_MODE`
- `VITE_SIGIL_STATE_OVERRIDE`
- `VITE_ECHO_TRACE_DEBUG`
- `VITE_SPIRAL_TRACE_DEBUG`
- `VITE_SPIRAL_API_SEAL`

Core server:

- `SPIRAL_API_SEAL`
- `SPIRAL_SIGIL_STATE`
- `SPIRAL_TRACE_DEBUG`
- `SIGIL_TRACE_BARRIER`
- `ALLOW_ECHO_OVERLAY`
- `ENABLE_HTTP_COMPRESSION`
- `HTTP_COMPRESSION_THRESHOLD`
- `LOG_API_RESPONSE_BODY`
- `LOG_API_RESPONSE_BODY_MAX`
- `SPIRAL_AUTH_REQUIRED`
- `SPIRAL_AUTH_JWT_SECRET`
- `SPIRAL_AUTH_SESSION_TTL_MS`
- `SPIRAL_AUTH_OAUTH_STATE_TTL_MS`
- `SPIRAL_ANON_SESSION_TTL_MS`
- `SPIRAL_AUTH_COOKIE_SECURE`

Storage and transcript:

- `SPIRAL_STORAGE_CACHE_DEFAULT`
- `SPIRAL_STORAGE_CACHE_TTL_MINUTES`
- `SPIRAL_STORAGE_PBKDF2_ITERATIONS`
- `SPIRAL_STORAGE_REFRESH_SKEW_MS`
- `IPFS_API_ENDPOINT`

OAuth and SSO:

- `GOOGLE_DRIVE_OAUTH_CLIENT_ID`
- `GOOGLE_DRIVE_OAUTH_CLIENT_SECRET`
- `GOOGLE_DRIVE_OAUTH_REDIRECT_URI`
- `GOOGLE_DRIVE_OAUTH_SCOPE`
- `GOOGLE_DRIVE_OAUTH_STATE_TTL_MS`
- `DROPBOX_OAUTH_CLIENT_ID`
- `DROPBOX_OAUTH_CLIENT_SECRET`
- `DROPBOX_OAUTH_REDIRECT_URI`
- `DROPBOX_OAUTH_SCOPE`
- `DROPBOX_OAUTH_STATE_TTL_MS`
- `GOOGLE_SSO_CLIENT_ID`
- `GOOGLE_SSO_CLIENT_SECRET`
- `GOOGLE_SSO_REDIRECT_URI`
- `GOOGLE_SSO_SCOPE`
- `MICROSOFT_SSO_CLIENT_ID`
- `MICROSOFT_SSO_CLIENT_SECRET`
- `MICROSOFT_SSO_REDIRECT_URI`
- `MICROSOFT_SSO_SCOPE`
- `MICROSOFT_SSO_TENANT`

Memory tuning:

- `MEMORY_CORE_MAX_AGE_DAYS`
- `MEMORY_PREFERENCE_MAX_AGE_DAYS`
- `MEMORY_PATTERN_MAX_AGE_DAYS`
- `MEMORY_CORE_HALF_LIFE_DAYS`
- `MEMORY_PREFERENCE_HALF_LIFE_DAYS`
- `MEMORY_PATTERN_HALF_LIFE_DAYS`
- `MEMORY_MIN_PROMPT_SCORE`
- `MEMORY_OVERLAP_WEIGHT`
- `MEMORY_RECENCY_WEIGHT`
- `MEMORY_CATEGORY_WEIGHT`
- `MEMORY_DECAY_WEIGHT`
- `MEMORY_FOLD_SIMILARITY_THRESHOLD`
- `MEMORY_PRUNE_MIN_SCORE`

Proposal execution:

- `SPIRAL_PROPOSAL_ROOT`
- `SPIRAL_CODEX_EXECUTION_ENABLED`
- `SPIRAL_CODEX_EXECUTOR`
- `SPIRAL_CODEX_COMMAND_TEMPLATE`
- `SPIRAL_CODEX_BINARY`
- `SPIRAL_OPENCLAW_COMMAND_TEMPLATE`
- `SPIRAL_CODEX_EXEC_TIMEOUT_MS`
- `SPIRAL_CODEX_VERIFY_COMMAND_TEMPLATE`
- `SPIRAL_CODEX_WORKTREE_ROOT`

Sigil signing:

- `SPIRAL_SIGIL_SIGNING_KEYS`
- `SPIRAL_SIGIL_SIGNING_ACTIVE_KEY`
- `SPIRAL_SIGIL_SIGNING_SECRET`

Route cache tuning:

- `ROUTE_CACHE_MAX_ENTRIES`
- `HISTORY_SNIPPET_CACHE_TTL_MS`
- `HISTORY_SELECTION_CACHE_TTL_MS`
- `RECENT_PROMPT_CACHE_TTL_MS`
- `PROMPT_METADATA_CACHE_TTL_MS`
- `RECENT_PROMPT_WINDOW_BUCKET_MS`
- `PROMPT_METADATA_TIME_BUCKET_MS`

Server process and parser tuning (supported by runtime code):

- `PORT`
- `HOST`
- `REUSE_PORT`
- `JSON_BODY_LIMIT`
- `IMPORT_JSON_BODY_LIMIT`
- `URLENCODED_BODY_LIMIT`

## Verification Commands

```powershell
npm run check
npm run test
npm run test:spiral-governance
```

## Notes

- This document is source-aligned to the current repository state, including self-inspection, self-evaluation, and self-distortion routing on both HTTP and veil invocation surfaces.
- No autonomous self-modification path exists in runtime behavior.
