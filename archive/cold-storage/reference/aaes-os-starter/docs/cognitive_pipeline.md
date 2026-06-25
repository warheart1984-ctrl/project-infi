# Cognitive Pipeline

Stages executed by `AAESOrchestrator.handle`:

| Stage | Engine | Input | Output |
|-------|--------|-------|--------|
| `perception` | `PerceptionEngine` | `AAESRequest` | `AAESContext` |
| `deliberation` | `DeliberationEngine` | `AAESContext` | `AAESPlan[]` |
| `planning` | `PlanningEngine` | plans + context | `AAESDecision` |
| `action` | `ActionEngine` | decision + context | `ActionResult[]` |
| `check` | `InvariantEngine` | each step | `InvariantResult` |

Each stage:

1. Builds an `AAESStep` record
2. Runs `InvariantEngine.check`
3. Logs via `AuditLogger.logStep`

Normative interfaces: [docs/contracts/AAES_OS_INTERFACE_V1.md](../../../docs/contracts/AAES_OS_INTERFACE_V1.md) §2.

Implementation: `src/orchestrator.ts`.
