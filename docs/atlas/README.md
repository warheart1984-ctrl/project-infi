# Architectural Atlas — Project Infinity / AAES-OS

A layered view of the 71 `@aaes-os/*` packages in the monorepo, organized by platform layer.

## How to Read This Atlas

- **Maturity**: `Declared` → `Partial` → `Verified` → `Promoted`
- **Dependencies**: only `@aaes-os/*` packages listed (external deps omitted)
- **Evidence links**: point to the source of truth for each package's status
- **Owner**: the capability team responsible for the package

## Layer Map

| Layer | Packages | Description |
|-------|----------|-------------|
| [Governance Kernel](#1-governance-kernel) | 14 | Constitutional backbone — invariants, fault journal, pattern ledger, governance loop, tri-core protocol |
| [Runtime Services](#2-runtime-services) | 20 | Live runtime surfaces — UCR, CIC, CSL, UL, CML/Voss, COE, CCC, GCRE, etc. |
| [Evidence & Provenance](#3-evidence--provenance) | 10 | Receipts, lineage ledgers, federation ledgers, trust root, attestation |
| [Simulation & Rendering](#4-simulation--rendering) | 6 | Mesh simulator, Nova substrate, platform mesh, PSOM, sovereign IDE |
| [Developer Tooling](#5-developer-tooling) | 10 | Coding assistant, AI CLI, release tools, platform CLI, SDK |
| [Products](#6-products) | 5 | Platform core, platform SDK, ops console, platform API, platform web |
| [Operations](#7-operations) | 6 | Healthcheck, telemetry, observability, Docker, CI/CD |

---

## 1. Governance Kernel

The constitutional backbone of AAES-OS. Every other layer depends on this layer for invariant enforcement, fault tracking, and governance decisions.

### 1.1 `@aaes-os/aaes-governance`
| Field | Value |
|-------|-------|
| **Responsibility** | InvariantEngine, FaultJournalStore, PatternLedger, DriftMetrics — the governance spine |
| **Maturity** | Verified |
| **Dependencies** | `@aaes-os/runledger` |
| **Dev Dependencies** | `@aaes-os/tri-core-protocol` |
| **Evidence** | `packages/aaes-governance/src/proofSurface.ts`, `tests/release/artifact-governance.test.ts` |
| **Owner** | Governance Team |

### 1.2 `@aaes-os/aais`
| Field | Value |
|-------|-------|
| **Responsibility** | AAIS immune protocol layer — flow (llm → jarvis → nova), capabilities, invariants |
| **Maturity** | Verified |
| **Dependencies** | `@aaes-os/aaes-governance`, `@aaes-os/tri-core-protocol` |
| **Evidence** | `packages/aais/src/AAISRuntime.ts`, `packages/aais/src/capabilities.ts` |
| **Owner** | AAIS Team |

### 1.3 `@aaes-os/tri-core-protocol`
| Field | Value |
|-------|-------|
| **Responsibility** | Tri-Core governance protocol types — the shared type contract for governance messages |
| **Maturity** | Verified |
| **Dependencies** | — |
| **Evidence** | `packages/tri-core-protocol/src/types.ts`, `packages/tri-core-protocol/src/patchLedger.ts` |
| **Owner** | Governance Team |

### 1.4 `@aaes-os/sovren`
| Field | Value |
|-------|-------|
| **Responsibility** | SOVREN cryptographic authority — token issuance and envelope signing |
| **Maturity** | Verified |
| **Dependencies** | — |
| **Evidence** | `packages/sovren/src/SovrenAuthority.ts` |
| **Owner** | Security Team |

### 1.5 `@aaes-os/kerno`
| Field | Value |
|-------|-------|
| **Responsibility** | KERNO compute scheduler — slot reservation and cache-hit-rate monitoring |
| **Maturity** | Verified |
| **Dependencies** | — |
| **Evidence** | `packages/kerno/src/KernoScheduler.ts` |
| **Owner** | Runtime Team |

### 1.6 `@aaes-os/ucr-attestation`
| Field | Value |
|-------|-------|
| **Responsibility** | UCR attestation token issuance and registration |
| **Maturity** | Verified |
| **Dependencies** | `@aaes-os/trust-root` |
| **Evidence** | `packages/ucr-attestation/src/ucrAttestation.ts` |
| **Owner** | Runtime Team |

### 1.7 `@aaes-os/trust-root`
| Field | Value |
|-------|-------|
| **Responsibility** | Trust root measurement and sealing primitives |
| **Maturity** | Verified |
| **Dependencies** | — |
| **Evidence** | `packages/trust-root/src/trustRoot.ts` |
| **Owner** | Security Team |

### 1.8 `@aaes-os/runtime-law-spine`
| Field | Value |
|-------|-------|
| **Responsibility** | Runtime law spine corridor admission and initialization |
| **Maturity** | Verified |
| **Dependencies** | `@aaes-os/trust-root`, `@aaes-os/ucr-attestation` |
| **Evidence** | `packages/runtime-law-spine/src/runtimeLawSpine.ts` |
| **Owner** | Runtime Team |

### 1.9 `@aaes-os/constitutional-enforcement-node`
| Field | Value |
|-------|-------|
| **Responsibility** | Constitutional Enforcement Node runtime primitive |
| **Maturity** | Verified |
| **Dependencies** | `@aaes-os/evidence-receipts`, `@aaes-os/mri-instrument`, `@aaes-os/runtime-law-spine` |
| **Evidence** | `packages/constitutional-enforcement-node/src/enforcementNode.ts` |
| **Owner** | Governance Team |

### 1.10 `@aaes-os/constitutional-evolution`
| Field | Value |
|-------|-------|
| **Responsibility** | Genesis Resonance Sacrifice constitutional evolution loop |
| **Maturity** | Verified |
| **Dependencies** | `@aaes-os/evidence-receipts`, `@aaes-os/meta-constitutional-calculus`, `@aaes-os/mri-instrument`, `@aaes-os/nimf` |
| **Evidence** | `packages/constitutional-evolution/src/constitutionalEvolution.ts` |
| **Owner** | Governance Team |

### 1.11 `@aaes-os/invariant-registry`
| Field | Value |
|-------|-------|
| **Responsibility** | Invariant registry and IDSL-1 compiler for AAES-OS |
| **Maturity** | Verified |
| **Dependencies** | `@aaes-os/constitutional-enforcement-node` |
| **Evidence** | `packages/invariant-registry/src/invariantRegistry.ts` |
| **Owner** | Governance Team |

### 1.12 `@aaes-os/meta-constitutional-calculus`
| Field | Value |
|-------|-------|
| **Responsibility** | CML-15 meta-constitutional collapse calculus |
| **Maturity** | Verified |
| **Dependencies** | `@aaes-os/evidence-receipts` |
| **Evidence** | `packages/meta-constitutional-calculus/src/metaConstitutionalCalculus.ts` |
| **Owner** | Governance Team |

### 1.13 `@aaes-os/nimf`
| Field | Value |
|-------|-------|
| **Responsibility** | NIMF institutional physics forecast model for AAES-OS MRI state |
| **Maturity** | Verified |
| **Dependencies** | `@aaes-os/mri-instrument` |
| **Evidence** | `packages/nimf/src/nimf.ts` |
| **Owner** | Governance Team |

### 1.14 `@aaes-os/mri-instrument`
| Field | Value |
|-------|-------|
| **Responsibility** | MRI v0.1 Continuity Index instrument for AAES-OS operators |
| **Maturity** | Verified |
| **Dependencies** | — |
| **Evidence** | `packages/mri-instrument/src/mriV2.ts` |
| **Owner** | Governance Team |

---

## 2. Runtime Services

Live runtime surfaces that implement the various AAES-OS subsystems. Each runtime surface is a governed execution path with its own domain, risk profile, and capability set.

### 2.1 `@aaes-os/ucr-runtime`
| Field | Value |
|-------|-------|
| **Responsibility** | UCRRuntime — governed execution shell v0.1 |
| **Maturity** | Verified |
| **Dependencies** | `@aaes-os/aaes-governance`, `@aaes-os/evidence-receipts`, `@aaes-os/runledger`, `@aaes-os/trace-bus`, `@aaes-os/tri-core-protocol` |
| **Evidence** | `packages/ucr-runtime/src/ucrRuntime.ts` |
| **Owner** | Runtime Team |

### 2.2 `@aaes-os/ccc-runtime`
| Field | Value |
|-------|-------|
| **Responsibility** | Constitutional Continuity Contract runtime surface |
| **Maturity** | Verified |
| **Dependencies** | — |
| **Evidence** | `packages/ccc-runtime/src/index.ts` |
| **Owner** | Runtime Team |

### 2.3 `@aaes-os/cic-runtime`
| Field | Value |
|-------|-------|
| **Responsibility** | Constitutional Inference Contract runtime surface |
| **Maturity** | Verified |
| **Dependencies** | — |
| **Evidence** | `packages/cic-runtime/src/index.ts` |
| **Owner** | Runtime Team |

### 2.4 `@aaes-os/csl-runtime`
| Field | Value |
|-------|-------|
| **Responsibility** | Constitutional Schema Layer runtime surface |
| **Maturity** | Verified |
| **Dependencies** | — |
| **Evidence** | `packages/csl-runtime/src/index.ts` |
| **Owner** | Runtime Team |

### 2.5 `@aaes-os/coe-runtime`
| Field | Value |
|-------|-------|
| **Responsibility** | Constitutional Operating Environment runtime surface |
| **Maturity** | Verified |
| **Dependencies** | — |
| **Evidence** | `packages/coe-runtime/src/index.ts` |
| **Owner** | Runtime Team |

### 2.6 `@aaes-os/cml-voss-runtime`
| Field | Value |
|-------|-------|
| **Responsibility** | CML-2, CVM-1, and The Voss Binding corpus runtime surface |
| **Maturity** | Verified |
| **Dependencies** | — |
| **Evidence** | `packages/cml-voss-runtime/src/index.ts` |
| **Owner** | Runtime Team |

### 2.7 `@aaes-os/gcre-sysmin`
| Field | Value |
|-------|-------|
| **Responsibility** | GCRE-SYSMIN-001 family registry and surface for the AAES-OS language family |
| **Maturity** | Verified |
| **Dependencies** | — |
| **Evidence** | `packages/gcre-sysmin/src/index.ts` |
| **Owner** | Runtime Team |

### 2.8 `@aaes-os/ul-runtime`
| Field | Value |
|-------|-------|
| **Responsibility** | Universal Language verb runtime surface — compiles UL actions into ISL-compatible intent |
| **Maturity** | Verified |
| **Dependencies** | — |
| **Evidence** | `packages/ul-runtime/src/index.ts` |
| **Owner** | Runtime Team |

### 2.9 `@aaes-os/isl-runtime`
| Field | Value |
|-------|-------|
| **Responsibility** | Intent Specification Layer runtime surface |
| **Maturity** | Verified |
| **Dependencies** | — |
| **Evidence** | `packages/isl-runtime/src/index.ts` |
| **Owner** | Runtime Team |

### 2.10 `@aaes-os/ceip-runtime`
| Field | Value |
|-------|-------|
| **Responsibility** | CEIP runtime — conformance, contracts, freeze, governance artifacts |
| **Maturity** | Verified |
| **Dependencies** | — |
| **Evidence** | `packages/ceip-runtime/src/index.ts` |
| **Owner** | Runtime Team |

### 2.11 `@aaes-os/operator-config`
| Field | Value |
|-------|-------|
| **Responsibility** | Operator configuration surface |
| **Maturity** | Partial |
| **Dependencies** | — |
| **Evidence** | `packages/operator-config/src/index.ts` |
| **Owner** | Ops Team |

### 2.12 `@aaes-os/ugr-runtime`
| Field | Value |
|-------|-------|
| **Responsibility** | UGR/UGQL/UPL/CRF runtime surface for governed knowledge, queries, packaging, and replay |
| **Maturity** | Verified |
| **Dependencies** | — |
| **Evidence** | `packages/ugr-runtime/src/runtime.ts` |
| **Owner** | Runtime Team |

### 2.13 `@aaes-os/ulx-governance`
| Field | Value |
|-------|-------|
| **Responsibility** | ULX governance and bytecode tracing layer |
| **Maturity** | Verified |
| **Dependencies** | `@aaes-os/aaes-governance`, `@aaes-os/tri-core-protocol` |
| **Evidence** | `packages/ulx-governance/src/ULXGovernanceRuntime.ts` |
| **Owner** | Governance Team |

### 2.14 `@aaes-os/ulx-vm`
| Field | Value |
|-------|-------|
| **Responsibility** | ULX virtual machine runtime |
| **Maturity** | Verified |
| **Dependencies** | `@aaes-os/ulx-governance` |
| **Evidence** | `packages/ulx-vm/src/ULXVirtualMachine.ts` |
| **Owner** | Governance Team |

### 2.15 `@aaes-os/urg`
| Field | Value |
|-------|-------|
| **Responsibility** | URG knowledge graph and authority layer |
| **Maturity** | Verified |
| **Dependencies** | `@aaes-os/aaes-governance`, `@aaes-os/tri-core-protocol` |
| **Evidence** | `packages/urg/src/URGRuntime.ts` |
| **Owner** | Governance Team |

### 2.16 `@aaes-os/sovereignty-ledger`
| Field | Value |
|-------|-------|
| **Responsibility** | Sovereignty ledger for AAES-OS enforcement decisions |
| **Maturity** | Verified |
| **Dependencies** | — |
| **Evidence** | `packages/sovereignty-ledger/src/sovereigntyLedger.ts` |
| **Owner** | Governance Team |

### 2.17 `@aaes-os/healthcheck-middleware`
| Field | Value |
|-------|-------|
| **Responsibility** | Kubernetes-compatible healthcheck middleware for AAES-OS services |
| **Maturity** | Verified |
| **Dependencies** | — |
| **Evidence** | `packages/healthcheck-middleware/src/index.ts` |
| **Owner** | Ops Team |

### 2.18 `@aaes-os/telemetry`
| Field | Value |
|-------|-------|
| **Responsibility** | AAES-OS telemetry and constitutional metrics |
| **Maturity** | Verified |
| **Dependencies** | — |
| **Evidence** | `packages/telemetry/src/metrics.ts` |
| **Owner** | Ops Team |

### 2.19 `@aaes-os/theta-codec`
| Field | Value |
|-------|-------|
| **Responsibility** | Theta glyph codec and entropy bridge for AAES-OS |
| **Maturity** | Verified |
| **Dependencies** | — |
| **Evidence** | `packages/theta-codec/src/thetaCodec.ts` |
| **Owner** | Runtime Team |

### 2.20 `@aaes-os/trace-bus`
| Field | Value |
|-------|-------|
| **Responsibility** | TraceBusClient — in-memory pub/sub trace event bus |
| **Maturity** | Verified |
| **Dependencies** | `@aaes-os/runledger` |
| **Evidence** | `packages/trace-bus/src/traceBus.ts` |
| **Owner** | Runtime Team |

---

## 3. Evidence & Provenance

Packages that generate, store, verify, and federate evidence and provenance data across the AAES-OS ecosystem.

### 3.1 `@aaes-os/evidence-receipts`
| Field | Value |
|-------|-------|
| **Responsibility** | AAES-OS evidence receipt generation for trust bundles |
| **Maturity** | Verified |
| **Dependencies** | `@aaes-os/aaes-governance`, `@aaes-os/mri-instrument`, `@aaes-os/trust-root`, `@aaes-os/ucr-attestation` |
| **Evidence** | `packages/evidence-receipts/src/ReceiptStore.ts`, `release/constitutional-release-receipt.json` |
| **Owner** | Evidence Team |

### 3.2 `@aaes-os/evidence-federation-ledger`
| Field | Value |
|-------|-------|
| **Responsibility** | FG-ECFL v1.0 — Evidence Canonical Federation Ledger |
| **Maturity** | Verified |
| **Dependencies** | — |
| **Evidence** | `packages/evidence-federation-ledger/src/ledger.ts` |
| **Owner** | Evidence Team |

### 3.3 `@aaes-os/evidence-lineage-ledger`
| Field | Value |
|-------|-------|
| **Responsibility** | FG-ECLL v1.0 — Evidence Canonical Lineage Ledger |
| **Maturity** | Verified |
| **Dependencies** | — |
| **Evidence** | `packages/evidence-lineage-ledger/src/ledger.ts` |
| **Owner** | Evidence Team |

### 3.4 `@aaes-os/evidence-sovereign-ledger`
| Field | Value |
|-------|-------|
| **Responsibility** | FG-ECSL v1.0 — Evidence Canonical Sovereign Ledger |
| **Maturity** | Verified |
| **Dependencies** | — |
| **Evidence** | `packages/evidence-sovereign-ledger/src/ledger.ts` |
| **Owner** | Evidence Team |

### 3.5 `@aaes-os/federation`
| Field | Value |
|-------|-------|
| **Responsibility** | Federation mesh — constitutional handshake between sovereign nodes |
| **Maturity** | Verified |
| **Dependencies** | `@aaes-os/aaes-governance`, `@aaes-os/sovren` |
| **Evidence** | `packages/federation/src/FederationManager.ts` |
| **Owner** | Governance Team |

### 3.6 `@aaes-os/canonical-authority-matrix`
| Field | Value |
|-------|-------|
| **Responsibility** | FG-CKHCAM v1.0 — Canonical Authority Matrix: hardware-level authority enforcement, reconstruction, validation and federation |
| **Maturity** | Verified |
| **Dependencies** | — |
| **Evidence** | `packages/canonical-authority-matrix/src/matrix.ts` |
| **Owner** | Governance Team |

### 3.7 `@aaes-os/canonical-replay-matrix`
| Field | Value |
|-------|-------|
| **Responsibility** | FG-CKHCRM v1.0 — Canonical Replay Matrix: deterministic hardware-level replay of all constitutional artifacts |
| **Maturity** | Verified |
| **Dependencies** | — |
| **Evidence** | `packages/canonical-replay-matrix/src/matrix.ts` |
| **Owner** | Governance Team |

### 3.8 `@aaes-os/canonical-stewardship-matrix`
| Field | Value |
|-------|-------|
| **Responsibility** | FG-CKHCSM v1.0 — Canonical Stewardship Matrix: hardware-level stewardship preservation, reconstruction, validation and federation |
| **Maturity** | Verified |
| **Dependencies** | — |
| **Evidence** | `packages/canonical-stewardship-matrix/src/matrix.ts` |
| **Owner** | Governance Team |

### 3.9 `@aaes-os/canonical-temporal-grid`
| Field | Value |
|-------|-------|
| **Responsibility** | FG-CKHCTG v1.0 — Canonical Temporal Grid: hardware-level temporal metadata enforcement, reconstruction, validation and federation |
| **Maturity** | Verified |
| **Dependencies** | — |
| **Evidence** | `packages/canonical-temporal-grid/src/grid.ts` |
| **Owner** | Governance Team |

### 3.10 `@aaes-os/cef-core`
| Field | Value |
|-------|-------|
| **Responsibility** | CEF v1.0 core — unified evidence schemas, Ajv validation, and profile registry |
| **Maturity** | Verified |
| **Dependencies** | — |
| **Evidence** | `packages/cef-core/src/index.ts`, `docs/release/cef/` |
| **Owner** | Evidence Team |

---

## 4. Simulation & Rendering

Packages that provide simulation, mesh networking, and rendering capabilities for the AAES-OS ecosystem.

### 4.1 `@aaes-os/nova-substrate`
| Field | Value |
|-------|-------|
| **Responsibility** | Rust NovaCoda substrate that exposes the live socket protocol surface |
| **Maturity** | Verified |
| **Dependencies** | — |
| **Evidence** | `packages/nova-substrate/src/` (Rust) |
| **Owner** | Nova Team |

### 4.2 `@aaes-os/nova-substrate-client`
| Field | Value |
|-------|-------|
| **Responsibility** | TypeScript client for NovaCoda Rust substrate |
| **Maturity** | Verified |
| **Dependencies** | — |
| **Evidence** | `packages/nova-substrate-client/src/NovaCodaClient.ts` |
| **Owner** | Nova Team |

### 4.3 `@aaes-os/nova-coda`
| Field | Value |
|-------|-------|
| **Responsibility** | Live NovaCoda runtime facade over the Rust substrate and TypeScript client |
| **Maturity** | Verified |
| **Dependencies** | `@aaes-os/nova-substrate-client` |
| **Evidence** | `packages/nova-coda/src/index.ts` |
| **Owner** | Nova Team |

### 4.4 `@aaes-os/nova-shell`
| Field | Value |
|-------|-------|
| **Responsibility** | Nova Coding Shell — Codex-style governed coding terminal |
| **Maturity** | Verified |
| **Dependencies** | `@aaes-os/aaes-governance`, `@aaes-os/tri-core-protocol`, `@aaes-os/ucr-runtime`, `@aaes-os/governed-runtime` |
| **Evidence** | `packages/nova-shell/src/NovaCodingShell.ts` |
| **Owner** | Coding Team |

### 4.5 `@aaes-os/platform-mesh`
| Field | Value |
|-------|-------|
| **Responsibility** | Multi-organism mesh networking — discovery, federation, and cross-organism workflows |
| **Maturity** | Verified |
| **Dependencies** | `@aaes-os/aaes-governance`, `@aaes-os/federation`, `@aaes-os/platform-core`, `@aaes-os/sovren` |
| **Evidence** | `packages/platform-mesh/src/MeshNetwork.ts` |
| **Owner** | Platform Team |

### 4.6 `@aaes-os/psom-mesh`
| Field | Value |
|-------|-------|
| **Responsibility** | Planet-Scale Organism Mesh — discovery, routing, governance enforcement, and failover |
| **Maturity** | Verified |
| **Dependencies** | `@aaes-os/aaes-governance`, `@aaes-os/federation`, `@aaes-os/platform-core`, `@aaes-os/sovren` |
| **Evidence** | `packages/psom-mesh/src/PsomMesh.ts` |
| **Owner** | Platform Team |

---

## 5. Developer Tooling

Packages that provide coding assistance, AI integration, release tooling, and developer-facing infrastructure.

### 5.1 `@aaes-os/coding-assistant`
| Field | Value |
|-------|-------|
| **Responsibility** | Governed multi-backend coding assistant — Nova, Infinity, and sandbox unified |
| **Maturity** | Verified |
| **Dependencies** | `@aaes-os/aais`, `@aaes-os/aaes-governance`, `@aaes-os/governed-runtime`, `@aaes-os/infinity-agents`, `@aaes-os/sovereignx-router`, `@aaes-os/nova-shell`, `@aaes-os/sandbox` |
| **Evidence** | `packages/coding-assistant/src/CodingAssistant.ts`, `tools/aais-cli.ts` |
| **Owner** | Coding Team |

### 5.2 `@aaes-os/governed-runtime`
| Field | Value |
|-------|-------|
| **Responsibility** | Universal coding adapter layer — CodingRouter, backends, and policy-driven routing |
| **Maturity** | Verified |
| **Dependencies** | `@aaes-os/aaes-governance`, `@aaes-os/kerno`, `@aaes-os/sovren` |
| **Evidence** | `packages/governed-runtime/src/router/CodingRouter.ts`, `packages/governed-runtime/src/adapters/` |
| **Owner** | Coding Team |

### 5.3 `@aaes-os/infinity-agents`
| Field | Value |
|-------|-------|
| **Responsibility** | Infinity Coding Agent — multi-step governed coding planner |
| **Maturity** | Verified |
| **Dependencies** | `@aaes-os/aaes-governance`, `@aaes-os/tri-core-protocol`, `@aaes-os/governed-runtime` |
| **Evidence** | `packages/infinity-agents/src/InfinityCodingAgent.ts` |
| **Owner** | Coding Team |

### 5.4 `@aaes-os/sandbox`
| Field | Value |
|-------|-------|
| **Responsibility** | Governed code-execution sandbox with module allowlisting |
| **Maturity** | Verified |
| **Dependencies** | — |
| **Evidence** | `packages/sandbox/src/GovernedSandbox.ts` |
| **Owner** | Coding Team |

### 5.5 `@aaes-os/sovereignx-router`
| Field | Value |
|-------|-------|
| **Responsibility** | SovereignX governed compute router — CPU governance over GPU acceleration with CIEMS-style limits |
| **Maturity** | Verified |
| **Dependencies** | — |
| **Evidence** | `packages/sovereignx-router/src/SovereignXRouter.ts` |
| **Owner** | Coding Team |

### 5.6 `@aaes-os/platform-cli`
| Field | Value |
|-------|-------|
| **Responsibility** | Organism CLI — unified command-line interface for the AAES super-platform |
| **Maturity** | Verified |
| **Dependencies** | `@aaes-os/lirl`, `@aaes-os/platform-core`, `@aaes-os/platform-sdk` |
| **Evidence** | `packages/platform-cli/src/cli.ts` |
| **Owner** | Platform Team |

### 5.7 `@aaes-os/platform-sdk`
| Field | Value |
|-------|-------|
| **Responsibility** | Official TypeScript/JavaScript SDK for PSOM + SGCE super-platform |
| **Maturity** | Verified |
| **Dependencies** | `@aaes-os/aaes-governance`, `@aaes-os/platform-core`, `@aaes-os/platform-mesh`, `@aaes-os/psom-mesh`, `@aaes-os/sgce`, `@aaes-os/sovren` |
| **Evidence** | `packages/platform-sdk/src/PlatformClient.ts` |
| **Owner** | Platform Team |

### 5.8 `@aaes-os/aais-vscode`
| Field | Value |
|-------|-------|
| **Responsibility** | VS Code extension for AAIS chat — governance-first coding assistant with local/cloud backends |
| **Maturity** | Partial |
| **Dependencies** | `@aaes-os/coding-assistant`, `@aaes-os/governed-runtime`, `@aaes-os/aais` |
| **Evidence** | `packages/aais-vscode/` |
| **Owner** | Coding Team |

### 5.9 `@aaes-os/architect-agent`
| Field | Value |
|-------|-------|
| **Responsibility** | Governed local coding agent with Ollama model support |
| **Maturity** | Partial |
| **Dependencies** | — |
| **Evidence** | `packages/architect-agent/src/architectAgent.ts` |
| **Owner** | Coding Team |

### 5.10 `@aaes-os/cef-certification`
| Field | Value |
|-------|-------|
| **Responsibility** | CEF Certification Engine stub — promotion gated by `@aaes-os/cef-core` |
| **Maturity** | Partial |
| **Dependencies** | `@aaes-os/cef-core` |
| **Evidence** | `packages/cef-certification/src/index.ts` |
| **Owner** | Evidence Team |

---

## 6. Products

Packages that provide the product-facing surfaces — the platform core, SDK, ops console, and API services.

### 6.1 `@aaes-os/platform-core`
| Field | Value |
|-------|-------|
| **Responsibility** | Super-platform core — governance profiles, capability versioning, billing, and API keys |
| **Maturity** | Verified |
| **Dependencies** | `@aaes-os/aaes-governance`, `@aaes-os/governed-runtime`, `@aaes-os/sovren` |
| **Evidence** | `packages/platform-core/src/PlatformService.ts` |
| **Owner** | Platform Team |

### 6.2 `@aaes-os/sgce`
| Field | Value |
|-------|-------|
| **Responsibility** | Self-Governing Capability Economy — tokenization, marketplace, provenance, and lifecycle |
| **Maturity** | Verified |
| **Dependencies** | `@aaes-os/platform-core` |
| **Evidence** | `packages/sgce/src/SgceEconomy.ts` |
| **Owner** | Platform Team |

### 6.3 `@aaes-os/coda-doc`
| Field | Value |
|-------|-------|
| **Responsibility** | Canonical Coda document catalog for CodaDoc, ISL, CML-2, CVM-1, the Voss Binding, and GCRE-SYSMIN-001 |
| **Maturity** | Verified |
| **Dependencies** | — |
| **Evidence** | `packages/coda-doc/src/index.ts` |
| **Owner** | Platform Team |

### 6.4 `@aaes-os/coda-runtime`
| Field | Value |
|-------|-------|
| **Responsibility** | Runtime facade for the Coda stack over the NovaCoda substrate |
| **Maturity** | Verified |
| **Dependencies** | `@aaes-os/coda-doc`, `@aaes-os/nova-coda` |
| **Evidence** | `packages/coda-runtime/src/index.ts` |
| **Owner** | Platform Team |

### 6.5 `@aaes-os/operator-surface`
| Field | Value |
|-------|-------|
| **Responsibility** | Operator surface for the AAES super-platform |
| **Maturity** | Partial |
| **Dependencies** | — |
| **Evidence** | `packages/operator-surface/` |
| **Owner** | Platform Team |

---

## 7. Operations

Packages that provide operational infrastructure — healthchecks, telemetry, observability, containerization, and CI/CD.

### 7.1 `@aaes-os/ops-console`
| Field | Value |
|-------|-------|
| **Responsibility** | Operations console — React UI + Express telemetry + Prometheus /metrics |
| **Maturity** | Verified |
| **Dependencies** | (service-level, see `services/ops-console/`) |
| **Evidence** | `services/ops-console/src/App.test.tsx`, `services/ops-console/src/server.test.ts` |
| **Owner** | Ops Team |

### 7.2 `@aaes-os/image-studio`
| Field | Value |
|-------|-------|
| **Responsibility** | AAIS-governed image studio using free cloud-hosted models (Pollinations keyless, Gemini free-tier key). Text-to-image + image-to-image. CLI + local web UI. |
| **Maturity** | Verified |
| **Dependencies** | `@aaes-os/aais` |
| **Evidence** | `packages/image-studio/src/` |
| **Owner** | Image Team |

### 7.3 `@aaes-os/cef-stewardship`
| Field | Value |
|-------|-------|
| **Responsibility** | CEF Stewardship stub — certificate lifecycle gated by `@aaes-os/cef-core` |
| **Maturity** | Partial |
| **Dependencies** | `@aaes-os/cef-core`, `@aaes-os/cef-certification` |
| **Evidence** | `packages/cef-stewardship/src/index.ts` |
| **Owner** | Evidence Team |

### 7.4 `@aaes-os/omega-stress-harness`
| Field | Value |
|-------|-------|
| **Responsibility** | Omega stress harness for AAES-OS constitutional enforcement |
| **Maturity** | Verified |
| **Dependencies** | `@aaes-os/constitutional-enforcement-node`, `@aaes-os/sovereignty-ledger` |
| **Evidence** | `packages/omega-stress-harness/src/omegaStressHarness.ts` |
| **Owner** | Governance Team |

### 7.5 `@aaes-os/transition-validation-pipeline`
| Field | Value |
|-------|-------|
| **Responsibility** | Transition Validation Pipeline for AAES-OS constitutional enforcement |
| **Maturity** | Verified |
| **Dependencies** | `@aaes-os/constitutional-enforcement-node` |
| **Evidence** | `packages/transition-validation-pipeline/src/transitionValidationPipeline.ts` |
| **Owner** | Governance Team |

### 7.6 `@aaes-os/ceip-runtime`
| Field | Value |
|-------|-------|
| **Responsibility** | CEIP runtime — conformance, contracts, freeze, governance artifacts |
| **Maturity** | Verified |
| **Dependencies** | — |
| **Evidence** | `packages/ceip-runtime/src/index.ts` |
| **Owner** | Runtime Team |

---

## Cross-Layer Dependency Graph

```
Governance Kernel
  ├─ aaes-governance ← runledger
  ├─ aais ← aaes-governance, tri-core-protocol
  ├─ tri-core-protocol
  ├─ sovren
  ├─ kerno
  ├─ ucr-attestation ← trust-root
  ├─ trust-root
  ├─ runtime-law-spine ← trust-root, ucr-attestation
  ├─ constitutional-enforcement-node ← evidence-receipts, mri-instrument, runtime-law-spine
  ├─ constitutional-evolution ← evidence-receipts, meta-constitutional-calculus, mri-instrument, nimf
  ├─ invariant-registry ← constitutional-enforcement-node
  ├─ meta-constitutional-calculus ← evidence-receipts
  ├─ nimf ← mri-instrument
  └─ mri-instrument

Runtime Services
  ├─ ucr-runtime ← aaes-governance, evidence-receipts, runledger, trace-bus, tri-core-protocol
  ├─ ccc-runtime
  ├─ cic-runtime
  ├─ csl-runtime
  ├─ coe-runtime
  ├─ cml-voss-runtime
  ├─ gcre-sysmin
  ├─ ul-runtime
  ├─ isl-runtime
  ├─ ceip-runtime
  ├─ operator-config
  ├─ ugr-runtime
  ├─ ulx-governance ← aaes-governance, tri-core-protocol
  ├─ ulx-vm ← ulx-governance
  ├─ urg ← aaes-governance, tri-core-protocol
  ├─ sovereignty-ledger
  ├─ healthcheck-middleware
  ├─ telemetry
  ├─ theta-codec
  └─ trace-bus ← runledger

Evidence & Provenance
  ├─ evidence-receipts ← aaes-governance, mri-instrument, trust-root, ucr-attestation
  ├─ evidence-federation-ledger
  ├─ evidence-lineage-ledger
  ├─ evidence-sovereign-ledger
  ├─ federation ← aaes-governance, sovren
  ├─ canonical-authority-matrix
  ├─ canonical-replay-matrix
  ├─ canonical-stewardship-matrix
  ├─ canonical-temporal-grid
  └─ cef-core

Simulation & Rendering
  ├─ nova-substrate (Rust)
  ├─ nova-substrate-client
  ├─ nova-coda ← nova-substrate-client
  ├─ nova-shell ← aaes-governance, tri-core-protocol, ucr-runtime, governed-runtime
  ├─ platform-mesh ← aaes-governance, federation, platform-core, sovren
  └─ psom-mesh ← aaes-governance, federation, platform-core, sovren

Developer Tooling
  ├─ coding-assistant ← aais, aaes-governance, governed-runtime, infinity-agents, sovereignx-router, nova-shell, sandbox
  ├─ governed-runtime ← aaes-governance, kerno, sovren
  ├─ infinity-agents ← aaes-governance, tri-core-protocol, governed-runtime
  ├─ sandbox
  ├─ sovereignx-router
  ├─ platform-cli ← lirl, platform-core, platform-sdk
  ├─ platform-sdk ← aaes-governance, platform-core, platform-mesh, psom-mesh, sgce, sovren
  ├─ aais-vscode ← coding-assistant, governed-runtime, aais
  ├─ architect-agent
  └─ cef-certification ← cef-core

Products
  ├─ platform-core ← aaes-governance, governed-runtime, sovren
  ├─ sgce ← platform-core
  ├─ coda-doc
  ├─ coda-runtime ← coda-doc, nova-coda
  └─ operator-surface

Operations
  ├─ ops-console (service)
  ├─ image-studio ← aais
  ├─ cef-stewardship ← cef-core, cef-certification
  ├─ omega-stress-harness ← constitutional-enforcement-node, sovereignty-ledger
  ├─ transition-validation-pipeline ← constitutional-enforcement-node
  └─ ceip-runtime
```

---

## Maturity Legend

| Level | Meaning |
|-------|---------|
| **Declared** | Package exists, has a README, but no tests or integration evidence |
| **Partial** | Package has tests passing, but not all surfaces are covered by release evidence |
| **Verified** | Package has passing tests AND is included in a verified release bundle |
| **Promoted** | Package is a production-critical surface with ongoing evidence in the OEL |

## Capability Owners

| Team | Packages |
|------|----------|
| **Governance Team** | aaes-governance, aais, tri-core-protocol, constitutional-enforcement-node, constitutional-evolution, invariant-registry, meta-constitutional-calculus, nimf, mri-instrument, ulx-governance, ulx-vm, urg, sovereignty-ledger, omega-stress-harness, transition-validation-pipeline, federation, canonical-authority-matrix, canonical-replay-matrix, canonical-stewardship-matrix, canonical-temporal-grid, cef-certification, cef-stewardship |
| **Runtime Team** | ucr-runtime, ccc-runtime, cic-runtime, csl-runtime, coe-runtime, cml-voss-runtime, gcre-sysmin, ul-runtime, isl-runtime, ceip-runtime, operator-config, ugr-runtime, theta-codec, trace-bus, runtime-law-spine, ucr-attestation, trust-root, kerno, healthcheck-middleware, telemetry |
| **Coding Team** | coding-assistant, governed-runtime, infinity-agents, sandbox, sovereignx-router, nova-shell, aais-vscode, architect-agent |
| **Evidence Team** | evidence-receipts, evidence-federation-ledger, evidence-lineage-ledger, evidence-sovereign-ledger, cef-core |
| **Platform Team** | platform-core, sgce, coda-doc, coda-runtime, operator-surface, platform-sdk, platform-cli, platform-mesh, psom-mesh, operator-config |
| **Nova Team** | nova-substrate, nova-substrate-client, nova-coda |
| **Image Team** | image-studio |
| **Ops Team** | ops-console |

---

*Last updated: 2026-08-02. Generated from `packages/*/package.json` metadata.*
