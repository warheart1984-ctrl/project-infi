# AAES-OS v1 (TypeScript)

Governed cognitive runtime package for AAIS — perception → deliberation → planning → policy-gated action execution with append-only trace auditing.

## Quick start

```bash
npm install
npm run build
npm test
npm start   # HTTP server on port 8080
```

## HTTP API

### `POST /aaes/execute`

```json
{
  "traceId": "trace_optional",
  "actorId": "operator-1",
  "scope": { "name": "code" },
  "prompt": "implement the fix for auth timeout"
}
```

Response includes `ok`, `traceId`, `steps`, `results`, and optional `decision` / `error`.

### `GET /aaes/trace/{traceId}`

Returns append-only steps recorded for the trace.

## Pipeline

| Stage | Module | Responsibility |
|-------|--------|----------------|
| Invariants | `DefaultInvariantEngine` | Block missing `traceId`, `actorId`, `scope.name` |
| Perception | `DefaultPerceptionEngine` | `normalizeInput` → `ctx.session.normalized` |
| Deliberation | `DefaultDeliberationEngine` | Candidate plans from `normalized.intent` |
| Planning | `DefaultPlanningEngine` | Score and select plan (targets `daniel.code` for code changes) |
| Action | `DefaultActionEngine` | Policy check → `DanielModule` execution |
| Audit | `TraceStoreAuditLogger` | `InMemoryTraceStore.appendStep` per pipeline step |

## Policy

- Rate limit: 30 requests / minute / actor
- Resource scope: `filesystem` / `network` require `scope.resources`
- **daniel.code**: denied unless `scope.name === "code"`

## Engineering layout

```
src/
  orchestrator.ts          # AAESOrchestrator.handle()
  server.ts                # HTTP :8080
  pipeline/                # perception, deliberation, planning, action_engine
  engines/                 # invariant + policy engines
  modules/daniel/          # DanielModule (daniel.* targets)
  governance/              # trace store + audit loggers
  uls/normalize.ts         # ingress normalization
tests/
  pipeline.test.ts
  omega.test.ts            # adversarial invariant/policy cases
```

Mythic labels (Coherence Fabric, Daniel cinematic executor, etc.) belong in comments and docs only.

## Contracts

- [AAES_OS_INTERFACE_V1.md](../docs/contracts/AAES_OS_INTERFACE_V1.md)
- [AAES_OS_V1_FORMAL_SPEC.md](../docs/contracts/AAES_OS_V1_FORMAL_SPEC.md)
