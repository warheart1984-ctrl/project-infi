# Docs Hub

This directory is the canonical documentation entrypoint for `E:\project-infi`.
Project Infinity is the umbrella blueprint for the workspace, while AAES-OS is the governed runtime workspace tracked by the scorecard.

## Canonical Links

- [Civilization OS (identity freeze + organ ledger)](./civilization-os/README.md)
- [Repository scorecard](./scorecards/project-infi.md)
- [Scorecard template](./scorecards/REPO_SCORECARD_TEMPLATE.md)
- [Canonical Replay & Evidence Contract](../docs-site/docs/governance/crec.md)
- [Constitutional Release Receipt](./release/constitutional-release-receipt.md)
- [Constitutional Release Record Template](./release/constitutional-release-record-template.md)
- [Launch Readiness Specification](./release/launch-readiness-specification.md)
- [ULX Merge Readiness Record](./release/ulx-merge-readiness-record.md)
- [CRK-1 release handoff index](./crk1/release/CRK1_V1_RELEASE_INDEX.md)
- [Constitutional Evidence Graph](./governance/constitutional-release-receipt.md)
- [Constitutional Laws of Intelligence](../docs-site/docs/governance/constitutional-laws-of-intelligence.md)
- [AAES-OS Specifications](./specifications/README.md)
- [Sovereign OS Constitutional Kernel (SOCK) Specification](./specifications/aaes-os-constitutional-kernel-specification.md)
- [SOCK Machine-Readable Schema](./specifications/aaes-os-constitutional-kernel.schema.json)
- [SOCK Control Plane Summary](./runtime/sovereign-os-constitutional-kernel-control-plane.md)
- [AIOS Constitutional Node Runtime v1](./specifications/aios-constitutional-node-runtime-v1.md)
- [ULX IDE integration map](./ulx/ulx-ide-integration.md)
- [Architecture tree](./architecture/README.md)
- [Architecture mapping](./architecture/AAES_OS_UCR_MAPPING.md)
- [Sovereign IDE runtime surface](./runtime/sovereign-ide.md)
- Live package surfaces: [@aaes-os/coda-doc](../packages/coda-doc/src/index.ts), [@aaes-os/coda-runtime](../packages/coda-runtime/src/index.ts), [@aaes-os/nova-substrate](../packages/nova-substrate/package.json), [@aaes-os/nova-coda](../packages/nova-coda/src/index.ts), [@aaes-os/ul-runtime](../packages/ul-runtime/src/index.ts), [@aaes-os/csl-runtime](../packages/csl-runtime/src/index.ts), [@aaes-os/isl-runtime](../packages/isl-runtime/src/index.ts), [@aaes-os/cic-runtime](../packages/cic-runtime/src/index.ts), [@aaes-os/ccc-runtime](../packages/ccc-runtime/src/index.ts), [@aaes-os/coe-runtime](../packages/coe-runtime/src/index.ts), [@aaes-os/cml-voss-runtime](../packages/cml-voss-runtime/src/index.ts), [@aaes-os/ugr-runtime](../packages/ugr-runtime/src/index.ts), and [@aaes-os/gcre-sysmin](../packages/gcre-sysmin/src/index.ts)
- [Production hardening evidence](./release/production-hardening/README.md)
- [AAES-OS Production Baseline v1.0](./release/production-baseline/aaes-os-v1.0/INDEX.md) — frozen operational deployment stack (evidence-producing reference environment)
- [Operational Evidence Layer (OEL)](./release/operational-evidence-layer/README.md) — Deployment Certificates + Evidence Records (ops projection of CREC)
- [Constitutional Evidence Framework (CEF) v1.0](./release/cef/README.md) — Charter, Certification Engine, profiles (CREC / OEL / CEL / Security / ModelEval)
- [External integration evidence](./release/external-integrations/README.md)
- [Docs-site overview](../docs-site/docs/overview.md)
- [Workspace README](../README.md)

## What this proves

The docs layer proves that the repository now has a canonical constitutional baseline, a reusable scorecard format, and a single place to inspect the evidence graph, remaining gaps, and the release receipt root node.
It also preserves the distinction between the umbrella blueprint and the mixed-maturity subsystems beneath it, so documentation does not overstate finished runtime status.
CIEMS, Constitutional Node, SovereignX, and related proof-surface concepts are partially implemented through docs-site pages and supporting packages, but the repo still treats them as mixed maturity rather than one fully finished product layer.

## Who it is for

- Operators who need a quick readiness check
- Contributors who need the repo constitution and evidence model
- Reviewers who need a stable audit surface

## How to verify it works

- Open [docs/scorecards/project-infi.md](./scorecards/project-infi.md)
- Open [docs-site/docs/overview.md](../docs-site/docs/overview.md)
- Confirm the README links resolve from the repository root

## How it fits the Constitutional Computing Stack

The docs hub is the evidence and audit layer that sits above implementation code and below human review. It explains governance, replay, verification, the repo's current truth boundary, and the constitutional evidence graph that everything traces back to.

## Filing map

- Current architecture and wiring guidance lives in [docs/architecture/AAES_OS_UCR_MAPPING.md](./architecture/AAES_OS_UCR_MAPPING.md)
- The architecture tree index lives in [docs/architecture/README.md](./architecture/README.md)
- The AAES-OS spec set lives in [docs/specifications/README.md](./specifications/README.md)
- The AIOS constitutional node runtime spec lives in [docs/specifications/aios-constitutional-node-runtime-v1.md](./specifications/aios-constitutional-node-runtime-v1.md)
- The Codex handoff packet template lives in [docs/crk1/release/CODEX_HANDOFF_PACKET.md](./crk1/release/CODEX_HANDOFF_PACKET.md)
- The Codex handoff workflow lives in [docs/crk1/release/CODEX_WORKFLOW.md](./crk1/release/CODEX_WORKFLOW.md)
- The Codex router bridge lives in [docs/crk1/release/CODEX_ROUTER_BRIDGE.md](./crk1/release/CODEX_ROUTER_BRIDGE.md)
- The Sovereign Router X product architecture lives in [docs/crk1/release/SOVEREIGN_ROUTER_X_PRODUCT_SPEC.md](./crk1/release/SOVEREIGN_ROUTER_X_PRODUCT_SPEC.md)
- The Sovereign Router X pricing worksheet lives in [docs/crk1/release/SOVEREIGN_ROUTER_X_PRICING.md](./crk1/release/SOVEREIGN_ROUTER_X_PRICING.md)
- The machine-readable Sovereign Router X pricing spec lives in [docs/crk1/release/SOVEREIGN_ROUTER_X_PRICING.spec.json](./crk1/release/SOVEREIGN_ROUTER_X_PRICING.spec.json)
- The CIS core principle draft lives in [docs/crk1/release/CIS_CORE_PRINCIPLES.md](./crk1/release/CIS_CORE_PRINCIPLES.md)
- The CIS conformance requirement set lives in [docs/crk1/release/CIS_CONFORMANCE_REQUIREMENTS.md](./crk1/release/CIS_CONFORMANCE_REQUIREMENTS.md)
- The CIS standards hierarchy and Research OS mapping live in [docs/crk1/release/CIS_STANDARDS_HIERARCHY.md](./crk1/release/CIS_STANDARDS_HIERARCHY.md)
- The CIS standards traceability matrix lives in [docs/crk1/release/CIS_STANDARDS_TRACEABILITY_MATRIX.md](./crk1/release/CIS_STANDARDS_TRACEABILITY_MATRIX.md)
- The machine-readable CIS hierarchy spec lives in [docs/crk1/release/CIS_STANDARDS_HIERARCHY.spec.json](./crk1/release/CIS_STANDARDS_HIERARCHY.spec.json)
- The generated CIS conformance suite input lives in [docs/crk1/release/CIS_CONFORMANCE_SUITE_INPUT.spec.json](./crk1/release/CIS_CONFORMANCE_SUITE_INPUT.spec.json)
- The CIS companion-spec registry lives in [docs/crk1/release/CIS_COMPANION_SPEC_REGISTRY.spec.json](./crk1/release/CIS_COMPANION_SPEC_REGISTRY.spec.json)
- The shared artifact governance model lives in [docs/crk1/release/ARTIFACT_GOVERNANCE_MODEL.md](./crk1/release/ARTIFACT_GOVERNANCE_MODEL.md)
- The artifact governance registry lives in [docs/crk1/release/ARTIFACT_GOVERNANCE_REGISTRY.spec.json](./crk1/release/ARTIFACT_GOVERNANCE_REGISTRY.spec.json)
- The external standards mapping layer lives in [docs/crk1/release/EXTERNAL_STANDARDS_MAPPING.md](./crk1/release/EXTERNAL_STANDARDS_MAPPING.md)
- The machine-readable external standards mapping lives in [docs/crk1/release/EXTERNAL_STANDARDS_MAPPING.spec.json](./crk1/release/EXTERNAL_STANDARDS_MAPPING.spec.json)
- The conformance suite generation rule lives in [docs/crk1/release/CIS_CONFORMANCE_SUITE_GENERATION.md](./crk1/release/CIS_CONFORMANCE_SUITE_GENERATION.md)
- The Codex handoff schemas live in [docs/crk1/release/codex-handoff-request.schema.json](./crk1/release/codex-handoff-request.schema.json) and [docs/crk1/release/codex-handoff-reply.schema.json](./crk1/release/codex-handoff-reply.schema.json)
- The Codex packet tools live in [tools/codex-handoff-cli.ts](/E:/project-infi/tools/codex-handoff-cli.ts), [tools/codex-handoff-prompt.ts](/E:/project-infi/tools/codex-handoff-prompt.ts), [tools/codex-handoff-ingest.ts](/E:/project-infi/tools/codex-handoff-ingest.ts), [tools/codex-handoff-router.ts](/E:/project-infi/tools/codex-handoff-router.ts), [tools/codex-handoff-orchestrator.ts](/E:/project-infi/tools/codex-handoff-orchestrator.ts), and [tools/codex-handoff-smoke.ts](/E:/project-infi/tools/codex-handoff-smoke.ts)
- The Sovereign IDE runtime surface lives in [docs/runtime/sovereign-ide.md](./runtime/sovereign-ide.md)
- The ULX IDE integration map lives in [docs/ulx/ulx-ide-integration.md](./ulx/ulx-ide-integration.md)
- The Hardware Governance Playbook lives in [docs/proof/platform/HARDWARE_GOVERNANCE_PLAYBOOK.md](./proof/platform/HARDWARE_GOVERNANCE_PLAYBOOK.md)
- Legacy runtime notes live in [docs/runtime/legacy/ai-organism.md](./runtime/legacy/ai-organism.md)
- Legacy architecture notes live in [docs/architecture/legacy/coding-assistant-architecture.md](./architecture/legacy/coding-assistant-architecture.md)

## Evidence Status Taxonomy

- Observed - verified by implementation, testing, or operational evidence
- Hypothesized - expected based on architecture but not yet verified
- Unknown - not yet evaluated

## What Is Still Left To Build

In priority order, the remaining work is:

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

The scorecard appendix now carries the detailed release-packaging and challenge artifacts for those same five surfaces, while this hub stays focused on the ordered runbook pointers.

## Proof & Challenge Surface

Every docs artifact should expose the same proof-and-challenge questions:

- What is being claimed?
- What evidence supports the claim?
- What evidence could invalidate the claim?
- Who verified it?
- Can it be independently replayed?
- What are the current truth boundaries?
- What is still unknown?
- What evidence is required to advance its maturity?

### Constitutional Proof Levels

- P0 - Concept
- P1 - Implemented
- P2 - Verified
- P3 - Operational
- P4 - Independently Verified
- P5 - Mission-Critical

### Evidence State Separation

- Implemented
- Verified
- Operational
- Commercially Available

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
