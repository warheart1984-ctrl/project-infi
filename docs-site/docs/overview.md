# Overview

AAES-OS is a governed cognitive runtime with a constitutional loop, persistent ledgering, and substrate-aware safety controls.
Project Infinity is the umbrella blueprint that aggregates finished subsystems and mixed-maturity surfaces; AAES-OS is the governed runtime workspace tracked in this overview.

## First entry point

If you are looking for the live implementation surfaces first, start with the [Live Surfaces](./runtime/live-surfaces.md)
hub. It is the most direct route to the live package surfaces now exposed in the docs site:

- [CodaDoc](./runtime/coda-doc.md)
- [CodaRuntime](./runtime/coda-runtime.md)
- [NovaCoda](./runtime/nova-coda.md)
- [Nova Substrate](./runtime/nova-substrate.md)
- [Nova Substrate Client](./runtime/nova-substrate-client.md)
- [ISL Runtime](./runtime/isl-runtime.md)
- [UGR Runtime](./runtime/ugr-runtime.md)
- [GCRE-SYSMIN-001](./runtime/gcre-sysmin.md)

## Canonical baseline

- Constitutional laws: [constitutional-laws-of-intelligence](./governance/constitutional-laws-of-intelligence.md)
- Canonical replay contract: [crec](./governance/crec.md)
- Constitutional release receipt: [constitutional-release-receipt](./governance/constitutional-release-receipt.md)
- Governance doctrine: [doctrine](./governance/doctrine.md)
- Governance invariants: [invariants](./governance/invariants.md)
- AAES-OS specifications: [specifications](./specifications/index.md)
- Unified knowledge and replay substrate: [UGR / UGQL / UPL / CRF specification](./specifications/ugr-ugql-upl-crf-specification.md)
- Federated ULX adapters: Project Infi, AAIS, Project Infinity Main, SovereignX Router, DirectX / SovereignX OS, and Vielthorn
- Runtime core: [runtime-core](./runtime/runtime-core.md)
- SovereignX router: governed CPU vs GPU routing under CIEMS-style limits
- Visualizers: [governance dashboard](./visualizer/governance-dashboard.md) and [Sovereign IDE](./visualizer/sovereign-ide.md)
- Constitutional Evidence Graph: release receipt root for every public view
- Runtime hub: [Live Surfaces](./runtime/live-surfaces.md)

## What this proves

This repository proves the AAES-OS workspace has a canonical constitutional baseline, a live scorecard, a consistent evidence model for build, test, smoke, replay, and documentation readiness, and a traceable path back to the constitutional laws of intelligence.

The operator-facing compute story now includes the SovereignX router and the visualizer surfaces for governance and the Sovereign IDE, and every public view resolves through the Constitutional Evidence Graph rooted in the release receipt.
The documentation landing page also surfaces the UGR / UGQL / UPL / CRF mirror so the governed knowledge and replay substrate is part of the first-click navigation path.
The runtime hub now gives the live package surfaces a first-class entry point, so runtime readers can jump straight to the implementation pages before reading the broader overview.
The maturity story remains split: the governance/runtime spine, docs-site, Nova Studio, ops-console, and SovereignX execution surfaces are verified prototype, while other surfaces stay scaffold or prototype until their evidence catches up.
CIEMS, Constitutional Node, SovereignX, and related proof-surface concepts are partially implemented through docs-site pages and supporting packages, but the repo still treats them as mixed maturity rather than one fully finished product layer.

## What Is Still Left To Build

1. Universal replay, audit, and documentation evidence for every promoted surface.
2. Release packaging and publish evidence for every surface that wants production status.
3. Remaining scaffold/prototype surfaces outside the verified prototype band.
4. Docs and runtime claims that still need explicit boundary language.

The ordered surface-by-surface checklist now lives in the scorecard and the repo root README so each promoted surface can be verified and packaged in dependency order.

The execution plan starts with replay/audit evidence for the governance/runtime spine, then proceeds through docs-site, Nova Studio, ops-console, and SovereignX before moving to release packaging.

For the first row, collect build output, test output, smoke output, replay bundle, run ledger entry, evidence graph snapshot, docs coverage manifest, and the claim boundary update.

For the docs-site row, collect docs build output, route graph snapshot, page-level citation manifest, replay trace, evidence graph linkage, and the docs claim boundary update.

For the Nova Studio row, collect studio build output, smoke output, replay trace, operator event trace, evidence graph linkage, and the studio claim boundary update.

For the ops-console row, collect console build output, service test output, smoke output, telemetry snapshot, operator trace, evidence graph linkage, and the console claim boundary update.

For the SovereignX execution surfaces row, collect execution proof output, control-plane trace, routing replay, release receipt linkage, operator-facing snapshot, and the SovereignX claim boundary update.

The scorecard appendix now carries the detailed release-packaging and challenge artifacts for those same five surfaces, while this overview stays focused on the ordered runbook pointers.

## Receipt-Driven Snapshot

- Layer 0 - Constitutional Ontology: Defines the constitutional vocabulary for Authority, Evidence, Verification, Compliance, and Truth.
- Current maturity: Verified Prototype for the governance/runtime spine, docs-site, Nova Studio, ops-console, and SovereignX execution surfaces; scaffold / prototype elsewhere.
- Operational status: Verified Prototype for the governance/runtime spine, docs-site, ops surfaces, Nova Studio, and SovereignX execution surfaces; other surfaces remain scaffold/prototype.
- Commercial readiness: Builder tier with prototype-to-verified-prototype progression.
- Proof level: P2-Verified for the governed baseline; lower levels apply to unfinished surfaces.
- Receipt hash: sha256:2bca968431d67fb744f90af08fb75e813521e7c8215cdc42c59a65971b534aab
- Verification timestamp: 2026-07-13T13:19:57.447Z

## Who it is for

- Operators who need a concise readiness view
- Contributors who need the repo constitution and gaps
- Reviewers who need a stable audit surface

## How to verify it works

- Open the workspace scorecard
- Open the architecture tree [docs/architecture/README.md](../../docs/architecture/README.md)
- Confirm the README links point to live docs
- Run the repository build and test commands listed in the scorecard

## How it fits the Constitutional Computing Stack

The docs layer sits above implementation and below human review. It explains the governance contract, the truth boundary, the current readiness of the workspace, and the shared constitutional vocabulary used across the stack.

The canonical release receipt is available in the governance docs for readers who want the release evidence package alongside the repo-level proof surface.

## Evidence Hierarchy

- Constitutional Governance: AAES governance packages, the scorecard template, CREC, and the constitutional laws
- Software Architecture: docs-site pages and linked workspace structure
- Implementation: Markdown content and documentation components
- Verification Evidence: scorecards, coverage manifests, and linked build/test output
- Operational Evidence: ops-console metrics and runtime routes
- Adoption Evidence: operator docs, README links, and reviewer-facing summaries

## Proof & Challenge Surface Runtime

### Identity

`docs-site` Proof & Challenge Surface Runtime mirror for the AAES-OS documentation layer.

### Purpose

Expose a standardized evidence layer for claims about the workspace baseline, governance contract, challenge evidence, and readiness state.

### Claim

The docs site mirrors the workspace's constitutional documentation layer and visible readiness baseline.
It also records the challenge evidence that could invalidate overstated claims, but it is not the runtime itself.

The machine-readable CIEMS Proof & Challenge Surface Runtime is exported by `@aaes-os/aaes-governance` so dashboards and studio tools can consume it directly.

### Evidence

- Static docs build output
- Canonical scorecard links
- Workspace README and docs hub references
- Documentation pages for governance, runtime, agents, and ULX
- Challenge evidence captured in scorecards and review notes

### Verification

Fresh docs build and smoke checks are required before this page can support a verified claim.

### Replay

Documentation can be rebuilt from source and re-read as a static artifact; replay depends on the upstream evidence it links to.

### Operational Status

Runnable static docs app that mirrors runtime reality, not the runtime itself.

### Truth Boundary

This page does not prove runtime completion or production readiness for unfinished surfaces.

### Challenge Boundary

This page does not prove that every claim has been fully invalidated or independently red-teamed.

### Constitutional Profile

- Purpose: workspace documentation and readiness baselines
- Authority: AAES governance packages, CREC, and the scorecard template
- Evidence model: docs output, scorecards, and linked build/test evidence
- Verification process: fresh build, smoke, and linked evidence review
- Compliance requirements: no claim beyond presented evidence
- Constitutional scope: documentation and readiness baselines
- Constitutional limits: does not replace the runtime or service build outputs

### Blindspots

- Docs-site is still a Proof & Challenge Surface Runtime mirror, not the runtime
- Some linked surfaces remain scaffolded or prototype-only
- Fresh replay verification is not fully universal
- Human reviewers can still over-read documentation polish as runtime completeness

### Adversarial Claims

- The docs site can be mistaken for product completion
- Scorecard references can be mistaken for live verification
- Readiness language can be overstated without current evidence
- A skeptical reviewer could claim the page lacks enough challenge evidence to prove the negative cases

### Battle Scars

- Placeholder lint gates
- Documentation previously raced ahead of runnable release surfaces
- Partial scaffolds were easy to overstate
- Earlier versions underweighted explicit challenge evidence

### Color-Team Readiness

| Team | Readiness |
|------|-----------|
| Red Team | Partial: the surface explains exposure but does not remove it |
| Blue Team | Partial: it points to evidence, but upstream verification still matters |
| Purple Team | Useful for reconciling claims and proofs |
| Green Team | Supports stable docs and repeatable checks |
| White Team | Anchors authority and truth boundaries |
| Black Team | Emerging: covert failure modes and hidden coupling are not yet exhaustively tested |

### Commercial Readiness

- Target CIEMS Tier: Builder
- Intended customer: operators, reviewers, contributors, and external collaborators
- Primary use case: canonical documentation and readiness inspection
- Value proposition: a transparent documentation Proof & Challenge Surface Runtime for the governed runtime workspace
- Current commercialization readiness: prototype-level documentation layer

### Next Evidence Required

- Surface-by-surface replay and audit evidence for the governance/runtime spine, docs-site, Nova Studio, ops-console, and SovereignX execution surfaces
- Surface-by-surface release packaging and publish evidence for those same promoted surfaces
- Fresh docs build verification where it still gates a promoted surface
- Wider consistency across all repo scorecards

## Constitutional Profile Extensions

- Constitutional Scope: workspace documentation and readiness baselines
- Constitutional Limits: does not replace the runtime or service build outputs
- Dependencies: docs hub, repo README, and workspace package evidence
- Stewardship / Maintainers: documentation and governance owners

## Maturity Progression

Scaffold -> Prototype -> Verified Prototype -> Reference Implementation -> Production Candidate -> Production

## Community and Commercialization

- Who benefits from this? Operators, reviewers, contributors, and external collaborators
- Who should contribute? People improving docs clarity, evidence traceability, and constitutional framing
- What customer problem does it solve? It gives a quick path to understanding readiness and scope
- What free capability does it provide? A canonical overview of the governed runtime workspace
- What commercial capability could eventually be built on top of it? Documentation, onboarding, and governance consulting materials

## Blindspots

- Docs-site is still an overview layer and not the final runnable product
- Some linked surfaces remain scaffolded or prototype-only
- Fresh replay verification is not fully universal

## Adversarial Claims

- The overview can be mistaken for runtime completion
- The scorecard can be mistaken for a fresh test run
- Readiness language can be overstated without evidence

## Battle Scars

- Placeholder lint and unfinished UI surfaces still need work
- Documentation has sometimes raced ahead of runnable release surfaces

## Color-Team Readiness

| Team | Readiness |
|------|-----------|
| Red Team | Partial: the overview explains exposure but does not remove it |
| Blue Team | Partial: it points to evidence, but upstream verification still matters |
| Purple Team | Useful for reconciling claims and proofs |
| Green Team | Supports stable docs and repeatable checks |
| White Team | Anchors authority and truth boundaries |
| Black Team | Emerging: covert failure modes and hidden coupling are not yet exhaustively tested |

## Governing Claim Rule

No repository should claim more than its evidence supports.















