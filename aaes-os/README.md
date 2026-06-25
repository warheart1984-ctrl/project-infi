# AAES-OS Monorepo

## Vision

AAES-OS provides a **stable, auditable spine** for agentic systems. It enforces invariants, journals faults, and supports governed evolution of behavior — enabling AI systems that are **deterministic, inspectable, and accountable** by design.

**v1.0 launch docs:** [docs/aaes-os/](../docs/aaes-os/) · **Roadmap:** [ROADMAP.md](ROADMAP.md) · **Contributing:** [CONTRIBUTING.md](CONTRIBUTING.md)

**Release ops:** [RELEASE_DASHBOARD.md](RELEASE_DASHBOARD.md) · [EVIDENCE_LEDGER.md](EVIDENCE_LEDGER.md) · [Replication](replication/README.md)

pnpm workspace for the AAES-OS **UCR spine** TypeScript packages. The legacy v1 cognitive runtime (`src/`, HTTP orchestrator) remains at the repo root for backward compatibility.

## Layout

```
aaes-os/
  runtime/crk1/           # CRK-1 reference runtime (CAS 1.0)
  sdk/
    generated/           # OpenAPI-derived types + client (pnpm sdk:generate)
    scripts/
      generate-sdk-types.ts
  api/                    # CAS 1.0 OpenAPI spec
  schemas/                # CAS 1.0 JSON Schema
  tests/cts/              # CAS 1.0 conformance test suite
  packages/
    runledger/          # RunLedgerStore — runs, spans, invariant links
    trace-bus/          # TraceBusClient — pub/sub trace events
    aaes-governance/    # InvariantEngine + FaultJournalStore (Phase 3 stub)
    ucr-runtime/        # UCRRuntime shell (Phase 3 stub)
    tri-core-protocol/  # Governance triad types (Phase 3 stub)
  services/
    ops-console/        # React UI + Express telemetry + Prometheus /metrics
  infra/
    grafana/            # aaes-os-dashboard.json
    prometheus/         # scrape config snippet
  tools/                # placeholder — CLI/dev tools
  docs/                 # workspace-local docs pointer
  tests/integration/    # cross-package spine tests
  src/                  # legacy AAES-OS v1 orchestrator (unchanged)
```

## Prerequisites

- Node.js ≥ 20
- [pnpm](https://pnpm.io/) ≥ 9

## Install

```bash
cd aaes-os
pnpm install
```

## Build

```bash
pnpm build          # all workspace packages
pnpm build:legacy   # legacy src/ orchestrator (npm/tsc root tsconfig)
```

## Test

```bash
pnpm test           # build packages + vitest (unit + integration)
pnpm test:packages  # per-package vitest where configured
pnpm test:legacy    # legacy node:test suite
```

## Ops Console

Telemetry UI and Prometheus metrics for drift, fault patterns, and patch effectiveness.

```bash
cd aaes-os
pnpm install
pnpm --filter @aaes-os/ops-console dev
```

- Vite UI: http://localhost:5173 (proxies `/telemetry` and `/metrics` to port 4000)
- API: http://localhost:4000
- `GET /telemetry` — JSON `{ drift, topPatterns, lastFaults, patchTimeline }`
- `GET /metrics` — Prometheus exposition (`aaes_drift_score`, `aaes_fault_events_total`, `aaes_fault_pattern_recurrence`)

Production:

```bash
pnpm --filter @aaes-os/ops-console build
pnpm --filter @aaes-os/ops-console start
```

Import Grafana dashboard from `infra/grafana/aaes-os-dashboard.json`. Prometheus scrape target: `localhost:4000` (see `infra/prometheus/prometheus.yml`).

Demo seed data (20 faults for `INV_FAIL_INV_OUTPUT_SHAPE` / `INV_FAIL_INV_DETERMINISM`, plus 2 patch samples) loads on server startup.

## Package dependency graph (Phase 2)

```
runledger  ←  trace-bus
    ↑            ↑
    └──── ucr-runtime (stub)
aaes-governance → runledger (types)
tri-core-protocol (standalone types)
```

## Mapping to Python spine

See [docs/architecture/AAES_OS_UCR_MAPPING.md](../docs/architecture/AAES_OS_UCR_MAPPING.md) at the repo root.

## Reasoning Contract

AAES-OS follows the workspace canonical AAIS reasoning handshake for
continuity-grade evaluations:
[`docs/contracts/AAIS_REASONING_PROFILE.md`](../docs/contracts/AAIS_REASONING_PROFILE.md).
CCS object schemas and examples are in
[`docs/contracts/CCS_CORE_SCHEMA.md`](../docs/contracts/CCS_CORE_SCHEMA.md),
[`schemas/ccs_core_objects.v1.json`](../schemas/ccs_core_objects.v1.json), and
[`fixtures/ccs/`](../fixtures/ccs/).

## Phase status

| Phase | Scope | Status |
|-------|--------|--------|
| 1 | Workspace shell, branded types, package.json/tsconfig | Done |
| 2 | In-memory RunStore, TraceBusClient, integration test | Done |
| 3 | Governance + UCR + tri-core stubs | Types/stubs only |
| 4 | Ops Console service | Done (`services/ops-console`) |
| 5 | Infra / persistence | Grafana + Prometheus snippets |
