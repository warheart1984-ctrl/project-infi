# AAES-OS Monorepo

pnpm workspace for the AAES-OS governed runtime, docs, and tooling packages. Project Infinity is the umbrella blueprint that aggregates finished subsystems and mixed-maturity surfaces, while AAES-OS is the governed runtime workspace tracked by the scorecard. The legacy v1 cognitive runtime (`src/`, HTTP orchestrator) remains at the repo root for backward compatibility.

Canonical scorecard: [docs/scorecards/project-infi.md](./docs/scorecards/project-infi.md)

Civilization OS freeze: [docs/civilization-os/README.md](./docs/civilization-os/README.md)

Docs hub: [docs/README.md](./docs/README.md)

The canonical finish criteria for this workspace live in [docs/scorecards/project-infi.md](./docs/scorecards/project-infi.md), including the nested `.runtime/e2e-operator-workspace` quarantine as ephemeral scratch output.

## Live Surfaces

The runtime surface split is now explicit in both the docs hub and the live packages:

- Live package surfaces: [@aaes-os/coda-doc](./packages/coda-doc/src/index.ts), [@aaes-os/coda-runtime](./packages/coda-runtime/src/index.ts), [@aaes-os/nova-substrate](./packages/nova-substrate/package.json), [@aaes-os/nova-coda](./packages/nova-coda/src/index.ts), [@aaes-os/ul-runtime](./packages/ul-runtime/src/index.ts), [@aaes-os/csl-runtime](./packages/csl-runtime/src/index.ts), [@aaes-os/isl-runtime](./packages/isl-runtime/src/index.ts), [@aaes-os/cic-runtime](./packages/cic-runtime/src/index.ts), [@aaes-os/ccc-runtime](./packages/ccc-runtime/src/index.ts), [@aaes-os/coe-runtime](./packages/coe-runtime/src/index.ts), [@aaes-os/cml-voss-runtime](./packages/cml-voss-runtime/src/index.ts), [@aaes-os/ugr-runtime](./packages/ugr-runtime/src/index.ts), and [@aaes-os/gcre-sysmin](./packages/gcre-sysmin/src/index.ts)
- CML-2, CVM-1, and The Voss Binding are now live as the CML/Voss runtime corpus surface
- Project Infinity remains the umbrella blueprint; AAES-OS is the governed runtime workspace that these live surfaces implement
- Production hardening evidence now lives in [docs/release/production-hardening/README.md](./docs/release/production-hardening/README.md), with read-only external service evidence in [docs/release/external-integrations/README.md](./docs/release/external-integrations/README.md)

## Constitutional Alignment

This monorepo operates under the **Unified Sovereign Specification v1.0.0** and **Prime Architect Constitutional Blueprint**:

- **7-Layer Architecture Model** - Constitutional Substrate (L0) through Governance & Observability (L6)
- **UCDD Standards Bundle v1.2.0** - Full compliance with S-001 through S-007
- **Section 2.1.2 Immutability Doctrine** - Constitutional artifacts are frozen
- **Section 2.1.3 Traceability Imperative** - All artifacts have traceability links

## Layout

```
aaes-os/
  packages/
    runledger/          # RunLedgerStore — runs, spans, invariant links
    trace-bus/          # TraceBusClient — pub/sub trace events
    aaes-governance/    # InvariantEngine + FaultJournalStore + governance loop
    ucr-runtime/        # Governed UCRRuntime execution path
    tri-core-protocol/  # Governance triad types + patch ledger
  services/
    ops-console/        # React UI + Express telemetry + Prometheus /metrics
  infra/
    grafana/            # aaes-os-dashboard.json
    prometheus/         # scrape config snippet
  tools/                # placeholder — CLI/dev tools
  docs/                 # workspace-local docs pointer
  sovereign-ide/        # Sovereign IDE scaffold (runtime, plugin, shell)
  tests/integration/    # cross-package spine tests
  src/                  # legacy AAES-OS v1 orchestrator (unchanged)
```

## Prerequisites

- Node.js ≥ 20
- [pnpm](https://pnpm.io/) ≥ 9

## Install

```bash
cd project-infi
pnpm install
```

## Release

```bash
pnpm run release
```

That command builds the release checksums, writes a Constitutional Release Receipt, packages the selected artifacts under `release/bundle/`, signs the bundle, and verifies the result against the manifest.

The release receipt is written to `release/constitutional-release-receipt.json` and mirrored into `release/bundle/constitutional-release-receipt.json`.

That receipt is also the root node of the Constitutional Evidence Graph, which powers the repo README, docs hub, scorecards, docs-site, Nova Studio, and ops-console views.

The Sovereign IDE scaffold lives in `sovereign-ide/` and is documented from the docs hub and runtime surfaces so it stays discoverable from the same workspace navigation.

## Constitutional Operations

This repo uses a local Git hook pipeline, not GitHub Actions, to zip the repo after major commits and send the snapshot to Dropbox.

```bash
pnpm run dropbox:install-hook
pnpm run dropbox:sync
pnpm run dropbox:watch
pnpm run dropbox:install-service
```

The hook lives in `.githooks/` and runs after commit, merge, and rewrite events. The watcher keeps an eye on non-commit edits and pushes dirty working-tree snapshots after a short debounce. Dropbox history is trimmed to the latest few snapshots per repo by default. Set `DROPBOX_SYNC_DISABLED=1` to suspend the hook temporarily, or stop the watcher process to pause live syncing.

The Windows service starts the watcher automatically as `AAESDropboxWatcherService`, runs under SCM, and writes its config/logs into `.runtime/dropbox-service/`. It uses the Dropbox API when `DROPBOX_TOKEN` is available, and falls back to a local Dropbox sync folder that the installer auto-detects from Dropbox desktop config unless you override it with `REPO_DROPBOX_SYNC_FOLDER_ROOT` or `DROPBOX_SYNC_FOLDER_ROOT`. If Dropbox has multiple roots, set `REPO_DROPBOX_ACCOUNT_SCOPE=business` or `REPO_DROPBOX_ACCOUNT_SCOPE=personal` before install to select the business or personal root explicitly. The `/automation` app now exposes this as a constitutional operations console with receipts, evidence, replay metadata, timeline events, and conformance status. Remove it with `pnpm run dropbox:uninstall-service` when you want to stop the auto-start path.

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
cd project-infi
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
    └──── ucr-runtime (governed path)
aaes-governance → runledger (types)
tri-core-protocol (governance triad + patch ledger)
```

## Architecture Mapping

See [docs/architecture/README.md](./docs/architecture/README.md) for the architecture tree and the current wiring map.

## Phase status

| Phase | Scope | Status |
|-------|--------|--------|
| 1 | Workspace shell, branded types, package.json/tsconfig | Done |
| 2 | In-memory RunStore, TraceBusClient, integration test | Done |
| 3 | Governance + UCR + tri-core wired | Governed runtime path wired with trace receipts and replay evidence |
| 4 | Ops Console service | Done (`services/ops-console`) |
| 5 | Infra / persistence | Grafana + Prometheus snippets |

The runtime blocker set (`packages/runledger`, `packages/trace-bus`, `packages/evidence-receipts`) is now treated as green for the governed runtime core.

## Canonical Scorecard Snapshot

| Field | Value |
|-------|-------|
| Repository purpose | AAES-OS governance spine, runtime packages, ops console, docs, and release scaffolding |
| Layer 0 - Constitutional Ontology | Defines the constitutional vocabulary for Authority, Evidence, Verification, Compliance, and Truth |
| Current maturity | Verified Prototype for the governance/runtime spine, docs-site, Nova Studio, ops-console, and SovereignX execution surfaces; scaffold / prototype elsewhere. |
| Build status | Fresh workspace build passes across the verified surfaces in this pass |
| Test status | Fresh package tests pass for the verified governance and ops surfaces in this pass |
| Smoke test status | Ops console, workspace docs, docs-site, and Nova Studio smoke paths are documented and verified; release smoke remains a next milestone |
| Documentation status | Canonical scorecard, docs hub, and docs-site overview are now wired |
| Replay/Audit capability | RunLedger, evidence receipts, docs coverage manifest, and fault journal artifacts are present |
| Known gaps | Production publication boundary selection, remaining scaffold/prototype hardening, and any write-capable external adapter deployments beyond the read-only verified service probes |
| Next milestone | Finish the surface-by-surface replay/audit checklist, then close the release packaging and publish checklist |
| Receipt hash | See `release/constitutional-release-receipt.json` |
| Verification timestamp | See `release/constitutional-release-receipt.json` |

## Proof Surface

| Field | Value |
|-------|-------|
| Identity | `project-infi` canonical proof surface for AAES-OS |
| Purpose | Connect governance, implementation, verification, and commercialization through a single evidence layer |
| Claim | The repo exposes a governed baseline with documented truth boundaries and replay paths |
| Evidence | Build output, test output, docs-site output, scorecards, and operational telemetry |
| Verification | Fresh build, test, smoke, replay, and docs checks are required for verified status |
| Replay | RunLedger, evidence receipts, and audit-linked docs provide continuity where available |
| Operational Status | Verified Prototype for the governance/runtime spine, docs-site, ops surfaces, Nova Studio, and SovereignX execution surfaces; other surfaces remain scaffold/prototype. |
| Truth Boundary | The repo does not claim production readiness for unfinished surfaces |
| Constitutional Profile | Authority, evidence, verification, compliance, scope, and limits are documented below |
| Blindspots | Universal replay/audit evidence, release packaging and publish evidence |
| Adversarial Claims | README or scorecard content can be mistaken for fresh verification without matching evidence |
| Battle Scars | Placeholder lint gates and overextended readiness language |
| Color-Team Readiness | Red/Blue/Purple/Green/Yellow/White readiness is documented in the scorecard and docs hub |
| Commercial Readiness | Builder tier with prototype-to-verified-prototype progression. |
| Receipt hash | See `release/constitutional-release-receipt.json` |
| Verification timestamp | See `release/constitutional-release-receipt.json` |
| Next Evidence Required | Universal replay/audit evidence, replay-linked documentation evidence, and release packaging / publish evidence |
| Proof Level | P2-Verified for the governed baseline; lower levels apply to unfinished surfaces. |

## Canonical Replay & Evidence Contract

The repository-wide constitutional interface is standardized as CREC:

- Intent
- Authority
- Evidence
- Verification
- Compliance
- Truth Boundary
- Replay Record
- Audit Trail
- Failure Path
- Proof Surface Level (P0-P5)
- Constitutional Maturity
- Commercial Readiness

The corresponding highest-level governance layer is the [Constitutional Laws of Intelligence](./docs-site/docs/governance/constitutional-laws-of-intelligence.md), which every repo claim should trace back to before it is treated as constitutionally reliable.

## Constitutional Freeze

Constitutional artifacts are frozen per Section 2.1.2 Immutability Doctrine. To check freeze status:

```bash
python constitutional_freeze.py check
```

To verify integrity:

```bash
python constitutional_freeze.py verify
```

## UCDD Compliance

This repository maintains full compliance with UCDD Standards Bundle v1.2.0:

- **S-001** - Conformance Evidence Requirements
- **S-002** - Traceability Linkage Protocol
- **S-003** - Version Sovereignty
- **S-004** - Layered Authority and Delegation
- **S-005** - Audit and Inspection Protocol
- **S-006** - Constitutional Amendment Governance
- **S-007** - AI Agent Compliance

## Constitutional References

- **Unified Sovereign Specification v1.0.0** - Section 2.1 Constitutional Foundations
- **UCDD Standards Bundle v1.2.0** - Standards S-001 through S-007
- **Prime Architect Constitutional Blueprint** - Immutability Doctrine

## Evidence Hierarchy

| Layer | Repo treatment |
|-------|----------------|
| Constitutional Governance | AAES governance packages, tri-core protocol, runtime governance rules |
| Software Architecture | workspace package layout, services, docs, simulation, and deployment scaffolds |
| Implementation | TypeScript packages, Express service code, UI scaffolds, and tests |
| Verification Evidence | package build output, package tests, docs coverage, and ledger-related records |
| Operational Evidence | ops-console telemetry, metrics, and service routes |
| Adoption Evidence | README docs, scorecards, and operator-facing documentation |

## Proof Surface Notes

- Every constitutional claim in this repository should point back to a proof surface field.
- Implemented, verified, operational, and commercially available are distinct states.
- No repository claim should exceed the evidence presented on its proof surface.
- The machine-readable CPS runtime now lives in `@aaes-os/aaes-governance` and can be consumed by dashboards or studio tools.

## Constitutional Profile Extensions

### Constitutional Scope

This repo governs AAES-OS runtime coordination, operator visibility, evidence capture, and constitutional documentation.

### Constitutional Limits

It does not yet govern the remaining scaffolded release and UI surfaces as production-complete artifacts.

### Dependencies

- pnpm workspace tooling
- TypeScript packages
- Ops console telemetry stack
- Docs site and scorecard artifacts

### Stewardship / Maintainers

The workspace steward is the AAES-OS / Nova constitutional runtime collaboration set.

## Maturity Progression

Scaffold -> Prototype -> Verified Prototype -> Reference Implementation -> Production Candidate -> Production

## Community and Commercialization

| Question | Answer |
|----------|--------|
| Who benefits from this? | Developers, operators, researchers, governance teams, and future collaborators |
| Who should contribute? | Contributors who can improve governance, docs, runtime wiring, and verification |
| What customer problem does it solve? | It reduces ambiguity by pairing constitutional governance with evidence-backed runtime surfaces |
| What free capability does it provide? | A working governed runtime workspace, docs, telemetry, and scorecards |
| What commercial capability could eventually be built on top of it? | Governed runtime deployments, operator tooling, advisory services, and productized evidence layers |

## Blindspots

- Known architectural blindspots: the docs-site and Nova Studio are still not fully production-runnable
- Known governance blindspots: some surfaces remain scaffolded and cannot yet claim verified readiness
- Known replay/audit blindspots: fresh replay verification is not yet complete across every surface
- Known operational blindspots: real ESLint and full release packaging are still missing
- Known adoption blindspots: external collaborators still need a simpler first-run path

## Adversarial Claims

- What adversarial actors could claim: that every surface is production ready
- What adversarial actors could exploit: the gap between scaffolded docs and fresh smoke verification
- What adversarial actors could misinterpret: a scorecard link as proof of total system completion
- What adversarial actors could falsify: readiness language without fresh test and smoke evidence
- What adversarial actors could bypass: informal assumptions that skip governance evidence

## Battle Scars

- Past failures: placeholder lint command
- Past regressions: docs and UI surfaces outpaced the verification story
- Past outages: not recorded in this scorecard yet
- Past misconfigurations: partial scaffolds presented as if they were finished products
- Past governance violations: overclaiming readiness without fresh evidence
- Past replay failures: replay coverage is present but not yet universal
- Past test failures: some surfaces still require fresh full verification
- Past architectural mistakes: the workspace grew faster than the canonical audit baseline

## Color-Team Readiness

| Team | Readiness |
|------|-----------|
| Red Team | Partial: attack surface exists in scaffolds and incomplete verification paths |
| Blue Team | Partial: monitoring and fault surfaces exist, but not every route is fully exercised |
| Purple Team | Emerging: attack/defense reconciliation is possible through docs and telemetry, not yet universal |
| Green Team | Partial: build/test stability exists in verified packages, but CI completeness is still evolving |
| Yellow Team | Partial: operator clarity is improved by scorecards, but not all surfaces are user-ready |
| White Team | Strongest current layer: governance, evidence language, and authority boundaries are documented |

## Governing Claim Rule

No repository should claim more than its evidence supports.

## Evidence Status Taxonomy

- Observed - verified by implementation, testing, or operational evidence
- Hypothesized - expected based on architecture but not yet verified
- Unknown - not yet evaluated

## Production Scope

Project Infinity is the umbrella blueprint, but this repository is not yet production-finished as a single runtime. The production claim remains limited to the verified prototype band for the governance/runtime spine, docs-site, Nova Studio, ops-console, and SovereignX execution surfaces.

What is still out of production scope:

1. Universal replay, audit, and documentation evidence for every promoted surface.
2. Release packaging and publish evidence for every surface that wants production status.
3. Remaining scaffold/prototype surfaces outside the verified prototype band.
4. Docs and runtime claims that still need explicit boundary language so they do not overstate production readiness.

Surface-by-surface checklist:

| Priority | Surface | Ownerable task |
|----------|---------|----------------|
| 1 | Governance/runtime spine | Refresh the build, test, smoke, and replay bundle; attach it to the evidence graph; keep the constitutional claims and receipts aligned. |
| 2 | docs-site | Verify the docs build, route graph, and page-level citations against the same receipt hash; record a fresh replay path. |
| 3 | Nova Studio | Record a fresh studio build, smoke, and replay trace for the operator shell. |
| 4 | ops-console | Preserve replayable telemetry, metrics, and operator actions; verify the console can reconstruct the same proof trail. |
| 5 | SovereignX execution surfaces | Capture execution proofs, control-plane traces, and replayable routing outcomes. |

Packaging follow-up:

| Priority | Surface | Ownerable task |
|----------|---------|----------------|
| 1 | Governance/runtime spine | Produce the release manifest, checksums, evidence package, and promotion record. |
| 2 | docs-site | Package the docs-site release artifact and record the publish step. |
| 3 | Nova Studio | Package the studio build and preserve the promotion evidence. |
| 4 | ops-console | Package the service artifact and record publish metadata. |
| 5 | SovereignX execution surfaces | Package the execution surfaces and keep the release traceable back to the verified build. |

This checklist is dependency-ordered: start with the governance/runtime spine, then move through docs-site, Nova Studio, ops-console, and SovereignX using the same receipt hash and claim boundary at each step.

Governance/runtime spine replay-audit packet: collect build output, test output, smoke output, replay bundle, run ledger entry, evidence graph snapshot, docs coverage manifest, and the claim boundary update before promoting the row.

docs-site replay-audit packet: collect docs build output, route graph snapshot, page-level citation manifest, replay trace, evidence graph linkage, and the docs claim boundary update before promoting the row.

Nova Studio replay-audit packet: collect studio build output, smoke output, replay trace, operator event trace, evidence graph linkage, and the studio claim boundary update before promoting the row.

ops-console replay-audit packet: collect console build output, service test output, smoke output, telemetry snapshot, operator trace, evidence graph linkage, and the console claim boundary update before promoting the row.

SovereignX execution surfaces replay-audit packet: collect execution proof output, control-plane trace, routing replay, release receipt linkage, operator-facing snapshot, and the SovereignX claim boundary update before promoting the row.

The scorecard appendix now carries the detailed release-packaging and challenge artifacts for those same five surfaces, while this README stays focused on the execution order and pointers.

## Scorecard Principles

- No repository should claim more than its evidence supports
- Every architectural claim should identify the evidence that supports it
- Every limitation should be explicitly documented rather than implied
- Every maturity level should be tied to objective verification criteria

## Future Validation

- Open research questions
- Planned verification work
- Planned red-team exercises
- Planned interoperability tests
- Planned performance benchmarks



