# CEF v1.0 Reference Implementation Plan

**Status:** Plan — CEF v1.0  
**Objective:** Implement CEF as a unified evidence architecture across AAES-OS, Sovereign X OS, and related systems.  
**Initial focus:** OEL (ops) and CREC (research); CEL, Security, and ModelEval follow.

## Phases

### Phase 1 — Core CEF substrate (Weeks 1–2)

**Define:**

- Unified Evidence Schema (core fields)
- Profile registry (CREC, OEL, CEL, Security, ModelEval)

**Implement:**

- Evidence object model in a shared library (e.g. `@aaes-os/cef-core` / `packages/cef-core`)
- JSON schema validation for all evidence objects

**Done when:** schemas in `docs/release/cef/schemas/` validate fixtures; package exports types + validate().

### Phase 2 — OEL profile implementation (Weeks 2–4)

**Implement:**

- OEL Evidence Record generator in AAES-OS CI/CD
- SBOM, digest, vulnerability, conformance, health, and policy gates

**Integrate:**

- Promotion workflow → Certification Engine → Baseline Certificate v1.0 (DRAFT)
- Storage under `docs/release/operational-evidence-layer/`

**Done when:** CI emits OEL evidence JSON; Baseline Certificate remains DRAFT/HOLD until gates pass.

### Phase 3 — CREC profile implementation (Weeks 4–6)

**Implement:**

- Research Evidence Records (experiments, datasets, models, results)
- Lineage tracking (inputs, methods, outputs, revisions)

**Integrate:**

- Promotion to Research Certificates via Certification Engine
- Storage under `docs/release/research-evidence-layer/`

### Phase 4 — Certification Engine service (Weeks 6–8)

**Implement:**

- Service/API for promotion decisions
- Authority validation (CAR), gate evaluation, signature, certificate creation

**Expose:**

- REST (and optional GraphQL) endpoints for promotion and certificate retrieval

### Phase 5 — Stewardship and dashboard (Weeks 8–10)

**Implement:**

- Stewardship states (unpromoted, active, renewal_pending, revoked, historical)
- Prometheus metrics and Grafana dashboards for evidence and certificates

See [observability/CEF_V1_STEWARDSHIP_DASHBOARD.md](./observability/CEF_V1_STEWARDSHIP_DASHBOARD.md).

## Risk controls

| Risk | Mitigation |
| --- | --- |
| Greenwashed “deployed” claims | DRAFT/HOLD until gates pass |
| Profile drift | CEF charter + shared schema |
| Unsigned promotions | CAR + signature required by engine |
| Lost replay | Mandatory `replay.instructions` |
