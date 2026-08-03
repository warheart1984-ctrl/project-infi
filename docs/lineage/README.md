# Architectural Lineage — Project Infinity / AAES-OS

Every capability answers two questions:

- **Where does it live?** → [Architectural Atlas](../atlas/README.md)
- **How did it evolve?** → This document

## How to Read This Lineage

Each entry traces a capability from its origin through its evolution to its current state. Entries are organized by layer to match the Atlas.

## Legend

| Symbol | Meaning |
|--------|---------|
| `🟢` | Active — current, maintained, evolving |
| `🟡` | Transitional — migrated or refactored, pending full adoption |
| `🔵` | Foundational — established the pattern, now stable |
| `⚪` | Historical — superseded or archived |
| `🔴` | Deprecated — scheduled for removal |

---

## 1. Governance Kernel Lineage

### 1.1 `@aaes-os/aaes-governance` — InvariantEngine + FaultJournal + PatternLedger

| Phase | Event | Date | Evidence |
|-------|-------|------|----------|
| `🔵` | **Origin** — InvariantEngine and FaultJournalStore established as the constitutional backbone | 2026-06 | `packages/aaes-governance/src/invariantEngine.ts`, `packages/aaes-governance/src/faultJournal.ts` |
| `🔵` | **PatternLedger added** — Merkle-tree ledger for governance events | 2026-06 | `packages/aaes-governance/src/patternLedger.ts` |
| `🟢` | **DriftMetrics integrated** — drift detection wired into governance loop | 2026-07 | `packages/aaes-governance/src/driftMetrics.ts` |
| `🟢` | **ProofSurface catalog** — structured proof surface for every governance artifact | 2026-07 | `packages/aaes-governance/src/proofSurfaceCatalog.ts` |
| `🟢` | **Freeze invariant** — ConstitutionalFreeze gates artifact mutation | 2026-07 | `packages/aaes-governance/src/freeze/ConstitutionalFreeze.ts` |
| `🟢` | **Current** — 71 packages depend on this as the governance spine | 2026-08 | `packages-metadata.json` |

### 1.2 `@aaes-os/aais` — AAIS Immune Protocol

| Phase | Event | Date | Evidence |
|-------|-------|------|----------|
| `🔵` | **Origin** — AAIS flow (llm → jarvis → nova) defined as the constitutional check pipeline | 2026-06 | `packages/aais/src/AAISRuntime.ts` |
| `🔵` | **Capabilities surfaced** — listAAISCapabilities / listAAISCodingCapabilities | 2026-06 | `packages/aais/src/capabilities.ts` |
| `🟢` | **AAISDoctrine** — governance rules for AAIS checks | 2026-07 | `packages/aais/src/AAISDoctrine.ts` |
| `🟢` | **CodingProvenance** — provenance tracking for coding operations | 2026-07 | `packages/aais/src/codingProvenance.ts` |
| `🟢` | **Current** — powers aais-cli and aais-vscode | 2026-08 | `tools/aais-cli.ts`, `packages/aais-vscode/` |

### 1.3 `@aaes-os/tri-core-protocol` — Tri-Core Governance Types

| Phase | Event | Date | Evidence |
|-------|-------|------|----------|
| `🔵` | **Origin** — TriCoreBus, TriCoreMessage, and governance types defined | 2026-06 | `packages/tri-core-protocol/src/types.ts` |
| `🔵` | **Patch ledger** — patchApply, patchLedger, patchProposals for constitutional patching | 2026-06 | `packages/tri-core-protocol/src/patchLedger.ts` |
| `🟢` | **Seed patches** — seedPatches for bootstrapping governance state | 2026-07 | `packages/tri-core-protocol/src/seedPatches.ts` |
| `🟢` | **Current** — foundational type contract for all governance packages | 2026-08 | 14 packages depend on it |

### 1.4 `@aaes-os/sovren` — SOVREN Cryptographic Authority

| Phase | Event | Date | Evidence |
|-------|-------|------|----------|
| `🔵` | **Origin** — AuthorityLevel enum and SovrenAuthority for token issuance | 2026-06 | `packages/sovren/src/SovrenAuthority.ts` |
| `🟢` | **Current** — used by federation, platform-core, governed-runtime | 2026-08 | 3 packages depend on it |

### 1.5 `@aaes-os/kerno` — KERNO Compute Scheduler

| Phase | Event | Date | Evidence |
|-------|-------|------|----------|
| `🔵` | **Origin** — slot reservation and cache-hit-rate monitoring | 2026-06 | `packages/kerno/src/KernoScheduler.ts` |
| `🟢` | **Current** — integrated into governed-runtime for backend scheduling | 2026-08 | 1 package depends on it |

### 1.6 `@aaes-os/trust-root` — Trust Root Measurement

| Phase | Event | Date | Evidence |
|-------|-------|------|----------|
| `🔵` | **Origin** — trust root measurement and sealing primitives | 2026-06 | `packages/trust-root/src/trustRoot.ts` |
| `🟢` | **Current** — used by ucr-attestation and runtime-law-spine | 2026-08 | 2 packages depend on it |

### 1.7 `@aaes-os/ucr-attestation` — UCR Attestation

| Phase | Event | Date | Evidence |
|-------|-------|------|----------|
| `🔵` | **Origin** — UCR attestation token issuance and registration | 2026-06 | `packages/ucr-attestation/src/ucrAttestation.ts` |
| `🟢` | **Current** — gates runtime admission via trust root | 2026-08 | 2 packages depend on it |

### 1.8 `@aaes-os/runtime-law-spine` — Runtime Law Spine

| Phase | Event | Date | Evidence |
|-------|-------|------|----------|
| `🔵` | **Origin** — corridor admission and initialization for runtime law | 2026-06 | `packages/runtime-law-spine/src/runtimeLawSpine.ts` |
| `🟢` | **Current** — governs how runtime packages enter the constitutional envelope | 2026-08 | 1 package depends on it |

### 1.9 `@aaes-os/constitutional-enforcement-node` — CEN

| Phase | Event | Date | Evidence |
|-------|-------|------|----------|
| `🔵` | **Origin** — constitutional enforcement node runtime primitive | 2026-06 | `packages/constitutional-enforcement-node/src/enforcementNode.ts` |
| `🟢` | **Current** — gates invariant enforcement for all runtime surfaces | 2026-08 | 3 packages depend on it |

### 1.10 `@aaes-os/constitutional-evolution` — CRE

| Phase | Event | Date | Evidence |
|-------|-------|------|----------|
| `🔵` | **Origin** — Genesis Resonance Sacrifice evolution loop | 2026-06 | `packages/constitutional-evolution/src/constitutionalEvolution.ts` |
| `🟢` | **Current** — drives constitutional evolution across the platform | 2026-08 | 1 package depends on it |

### 1.11 `@aaes-os/invariant-registry` — IDSL-1 Compiler

| Phase | Event | Date | Evidence |
|-------|-------|------|----------|
| `🔵` | **Origin** — invariant registry and IDSL-1 compiler | 2026-06 | `packages/invariant-registry/src/invariantRegistry.ts` |
| `🟢` | **Current** — compiles invariants for enforcement nodes | 2026-08 | 1 package depends on it |

### 1.12 `@aaes-os/meta-constitutional-calculus` — CML-15

| Phase | Event | Date | Evidence |
|-------|-------|------|----------|
| `🔵` | **Origin** — meta-constitutional collapse calculus | 2026-06 | `packages/meta-constitutional-calculus/src/index.ts` |
| `🟢` | **Current** — provides the calculus for constitutional evolution | 2026-08 | 1 package depends on it |

### 1.13 `@aaes-os/nimf` — NIMF Forecast Model

| Phase | Event | Date | Evidence |
|-------|-------|------|----------|
| `🔵` | **Origin** — institutional physics forecast model for MRI state | 2026-06 | `packages/nimf/src/nimf.ts` |
| `🟢` | **Current** — drives MRI-based governance decisions | 2026-08 | 1 package depends on it |

### 1.14 `@aaes-os/mri-instrument` — MRI Continuity Index

| Phase | Event | Date | Evidence |
|-------|-------|------|----------|
| `🔵` | **Origin** — MRI v0.1 Continuity Index instrument | 2026-06 | `packages/mri-instrument/src/mriV2.ts` |
| `🟢` | **Current** — provides continuity metrics for all governance decisions | 2026-08 | 5 packages depend on it |

---

## 2. Runtime Services Lineage

### 2.1 `@aaes-os/ucr-runtime` — UCR Runtime

| Phase | Event | Date | Evidence |
|-------|-------|------|----------|
| `🔵` | **Origin** — governed execution shell v0.1 | 2026-06 | `packages/ucr-runtime/src/ucrRuntime.ts` |
| `🟢` | **AgentBridge added** — bridges UCR to agent execution | 2026-07 | `packages/ucr-runtime/src/AgentBridge.ts` |
| `🟢` | **SubstrateBridge added** — bridges UCR to NovaCoda substrate | 2026-07 | `packages/ucr-runtime/src/SubstrateBridge.ts` |
| `🟢` | **Current** — core runtime surface for all governed execution | 2026-08 | 1 package depends on it |

### 2.2 `@aaes-os/ccc-runtime` — Constitutional Continuity Contract

| Phase | Event | Date | Evidence |
|-------|-------|------|----------|
| `🔵` | **Origin** — live runtime surface for replay contracts, timelines, lineage invariants | 2026-06 | `packages/ccc-runtime/src/index.ts` |
| `🟢` | **Current** — governs contract replay and continuity checks | 2026-08 | No dependencies |

### 2.3 `@aaes-os/cic-runtime` — Constitutional Inference Contract

| Phase | Event | Date | Evidence |
|-------|-------|------|----------|
| `🔵` | **Origin** — live runtime surface for deterministic rules and semantic conclusions | 2026-06 | `packages/cic-runtime/src/index.ts` |
| `🟢` | **Current** — governs inference contract execution | 2026-08 | No dependencies |

### 2.4 `@aaes-os/csl-runtime` — Constitutional Schema Layer

| Phase | Event | Date | Evidence |
|-------|-------|------|----------|
| `🔵` | **Origin** — live runtime surface for governed artifact schemas | 2026-06 | `packages/csl-runtime/src/index.ts` |
| `🟢` | **Current** — governs schema evolution contracts | 2026-08 | No dependencies |

### 2.5 `@aaes-os/coe-runtime` — Constitutional Operating Environment

| Phase | Event | Date | Evidence |
|-------|-------|------|----------|
| `🔵` | **Origin** — live runtime surface for governed routes, schedules, promotion workflows | 2026-06 | `packages/coe-runtime/src/index.ts` |
| `🟢` | **Current** — governs operational workflows | 2026-08 | No dependencies |

### 2.6 `@aaes-os/cml-voss-runtime` — CML/Voss Binding

| Phase | Event | Date | Evidence |
|-------|-------|------|----------|
| `🔵` | **Origin** — live runtime surface for CML-2, CVM-1, Voss Binding corpus | 2026-06 | `packages/cml-voss-runtime/src/index.ts` |
| `🟢` | **Current** — governs corpus-level runtime surfaces | 2026-08 | No dependencies |

### 2.7 `@aaes-os/gcre-sysmin` — GCRE-SYSMIN-001

| Phase | Event | Date | Evidence |
|-------|-------|------|----------|
| `🔵` | **Origin** — family registry for the AAES-OS language family | 2026-06 | `packages/gcre-sysmin/src/index.ts` |
| `🟢` | **Current** — governs language family surface | 2026-08 | No dependencies |

### 2.8 `@aaes-os/ul-runtime` — Universal Language Runtime

| Phase | Event | Date | Evidence |
|-------|-------|------|----------|
| `🔵` | **Origin** — live runtime surface for compiling UL actions into ISL-compatible intent | 2026-06 | `packages/ul-runtime/src/index.ts` |
| `🟢` | **Current** — governs UL-to-ISL compilation | 2026-08 | No dependencies |

### 2.9 `@aaes-os/isl-runtime` — Intent Specification Layer

| Phase | Event | Date | Evidence |
|-------|-------|------|----------|
| `🔵` | **Origin** — live runtime surface for governed intents, evidence, authority | 2026-06 | `packages/isl-runtime/src/index.ts` |
| `🟢` | **Current** — governs intent specification execution | 2026-08 | No dependencies |

### 2.10 `@aaes-os/ceip-runtime` — CEIP Runtime

| Phase | Event | Date | Evidence |
|-------|-------|------|----------|
| `🔵` | **Origin** — conformance, contracts, freeze, governance artifacts | 2026-06 | `packages/ceip-runtime/src/index.ts` |
| `🟢` | **Current** — governs CEIP conformance checks | 2026-08 | No dependencies |

### 2.11 `@aaes-os/operator-config` — Operator Configuration

| Phase | Event | Date | Evidence |
|-------|-------|------|----------|
| `🟡` | **Origin** — operator configuration surface (stub) | 2026-06 | `packages/operator-config/src/index.ts` |
| `🟡` | **Current** — partial, needs full operator config surface | 2026-08 | No dependencies |

### 2.12 `@aaes-os/ugr-runtime` — UGR Runtime

| Phase | Event | Date | Evidence |
|-------|-------|------|----------|
| `🔵` | **Origin** — governed knowledge, queries, packaging, and replay surface | 2026-06 | `packages/ugr-runtime/src/runtime.ts` |
| `🟢` | **Adapters added** — Neo4j, pgvector, postgres drivers | 2026-07 | `packages/ugr-runtime/src/adapters/` |
| `🟢` | **Current** — multi-driver governed knowledge runtime | 2026-08 | No dependencies |

### 2.13 `@aaes-os/ulx-governance` — ULX Governance

| Phase | Event | Date | Evidence |
|-------|-------|------|----------|
| `🔵` | **Origin** — ULX governance and bytecode tracing layer | 2026-06 | `packages/ulx-governance/src/ULXGovernanceRuntime.ts` |
| `🟢` | **Compiler added** — ConstitutionalCompiler for ULX bytecode | 2026-07 | `packages/ulx-governance/src/ConstitutionalCompiler.ts` |
| `🟢` | **Current** — governs ULX bytecode tracing and validation | 2026-08 | 1 package depends on it |

### 2.14 `@aaes-os/ulx-vm` — ULX Virtual Machine

| Phase | Event | Date | Evidence |
|-------|-------|------|----------|
| `🔵` | **Origin** — ULX virtual machine runtime | 2026-06 | `packages/ulx-vm/src/ULXVirtualMachine.ts` |
| `🟢` | **Current** — executes ULX bytecode under governance | 2026-08 | 1 package depends on it |

### 2.15 `@aaes-os/urg` — URG Knowledge Graph

| Phase | Event | Date | Evidence |
|-------|-------|------|----------|
| `🔵` | **Origin** — URG knowledge graph and authority layer | 2026-06 | `packages/urg/src/URGRuntime.ts` |
| `🟢` | **Current** — governs knowledge graph authority and queries | 2026-08 | 2 packages depend on it |

### 2.16 `@aaes-os/sovereignty-ledger` — Sovereignty Ledger

| Phase | Event | Date | Evidence |
|-------|-------|------|----------|
| `🔵` | **Origin** — sovereignty ledger for enforcement decisions | 2026-06 | `packages/sovereignty-ledger/src/sovereigntyLedger.ts` |
| `🟢` | **Current** — records all sovereignty enforcement events | 2026-08 | No dependencies |

### 2.17 `@aaes-os/healthcheck-middleware` — Healthcheck Middleware

| Phase | Event | Date | Evidence |
|-------|-------|------|----------|
| `🔵` | **Origin** — Kubernetes-compatible healthcheck middleware | 2026-06 | `packages/healthcheck-middleware/src/index.ts` |
| `🟢` | **Current** — provides healthcheck endpoints for all AAES-OS services | 2026-08 | No dependencies |

### 2.18 `@aaes-os/telemetry` — Telemetry

| Phase | Event | Date | Evidence |
|-------|-------|------|----------|
| `🔵` | **Origin** — AAES-OS telemetry and constitutional metrics | 2026-06 | `packages/telemetry/src/metrics.ts` |
| `🟢` | **Current** — provides constitutional metrics for all governance decisions | 2026-08 | No dependencies |

### 2.19 `@aaes-os/theta-codec` — Theta Glyph Codec

| Phase | Event | Date | Evidence |
|-------|-------|------|----------|
| `🔵` | **Origin** — Theta glyph codec and entropy bridge | 2026-06 | `packages/theta-codec/src/thetaCodec.ts` |
| `🟢` | **Current** — governs glyph encoding and entropy bridging | 2026-08 | No dependencies |

### 2.20 `@aaes-os/trace-bus` — TraceBusClient

| Phase | Event | Date | Evidence |
|-------|-------|------|----------|
| `🔵` | **Origin** — in-memory pub/sub trace event bus | 2026-06 | `packages/trace-bus/src/traceBus.ts` |
| `🟢` | **Console sink added** — console-sink for trace event output | 2026-07 | `packages/trace-bus/src/console-sink.ts` |
| `🟢` | **Current** — provides trace event bus for all governance operations | 2026-08 | 1 package depends on it |

---

## 3. Evidence & Provenance Lineage

### 3.1 `@aaes-os/evidence-receipts` — Evidence Receipts

| Phase | Event | Date | Evidence |
|-------|-------|------|----------|
| `🔵` | **Origin** — AAES-OS evidence receipt generation for trust bundles | 2026-06 | `packages/evidence-receipts/src/ReceiptStore.ts` |
| `🔵` | **ReceiptStore** — immutable receipt store with Merkle verification | 2026-06 | `packages/evidence-receipts/src/ReceiptStore.ts` |
| `🟢` | **Current** — generates and verifies all constitutional release receipts | 2026-08 | 3 packages depend on it |

### 3.2 `@aaes-os/evidence-federation-ledger` — ECFL

| Phase | Event | Date | Evidence |
|-------|-------|------|----------|
| `🔵` | **Origin** — FG-ECFL v1.0 — Evidence Canonical Federation Ledger | 2026-06 | `packages/evidence-federation-ledger/src/ledger.ts` |
| `🟢` | **Current** — records canonical federated evidence metadata | 2026-08 | No dependencies |

### 3.3 `@aaes-os/evidence-lineage-ledger` — ECLL

| Phase | Event | Date | Evidence |
|-------|-------|------|----------|
| `🔵` | **Origin** — FG-ECLL v1.0 — Evidence Canonical Lineage Ledger | 2026-06 | `packages/evidence-lineage-ledger/src/ledger.ts` |
| `🟢` | **Current** — records canonical evidence lineage metadata | 2026-08 | No dependencies |

### 3.4 `@aaes-os/evidence-sovereign-ledger` — ECSL

| Phase | Event | Date | Evidence |
|-------|-------|------|----------|
| `🔵` | **Origin** — FG-ECSL v1.0 — Evidence Canonical Sovereign Ledger | 2026-06 | `packages/evidence-sovereign-ledger/src/ledger.ts` |
| `🟢` | **Current** — records canonical sovereign evidence metadata | 2026-08 | No dependencies |

### 3.5 `@aaes-os/federation` — Federation Mesh

| Phase | Event | Date | Evidence |
|-------|-------|------|----------|
| `🔵` | **Origin** — constitutional handshake between sovereign nodes | 2026-06 | `packages/federation/src/FederationManager.ts` |
| `🟢` | **Current** — governs cross-node federation | 2026-08 | 2 packages depend on it |

### 3.6 `@aaes-os/canonical-authority-matrix` — CKHCAM

| Phase | Event | Date | Evidence |
|-------|-------|------|----------|
| `🔵` | **Origin** — FG-CKHCAM v1.0 — hardware-level authority enforcement | 2026-06 | `packages/canonical-authority-matrix/src/matrix.ts` |
| `🟢` | **Current** — enforces authority at the hardware level | 2026-08 | No dependencies |

### 3.7 `@aaes-os/canonical-replay-matrix` — CKHCRM

| Phase | Event | Date | Evidence |
|-------|-------|------|----------|
| `🔵` | **Origin** — FG-CKHCRM v1.0 — deterministic hardware-level replay | 2026-06 | `packages/canonical-replay-matrix/src/matrix.ts` |
| `🟢` | **Current** — replays all constitutional artifacts deterministically | 2026-08 | No dependencies |

### 3.8 `@aaes-os/canonical-stewardship-matrix` — CKHCSM

| Phase | Event | Date | Evidence |
|-------|-------|------|----------|
| `🔵` | **Origin** — FG-CKHCSM v1.0 — hardware-level stewardship preservation | 2026-06 | `packages/canonical-stewardship-matrix/src/matrix.ts` |
| `🟢` | **Current** — preserves stewardship at the hardware level | 2026-08 | No dependencies |

### 3.9 `@aaes-os/canonical-temporal-grid` — CKHCTG

| Phase | Event | Date | Evidence |
|-------|-------|------|----------|
| `🔵` | **Origin** — FG-CKHCTG v1.0 — hardware-level temporal metadata enforcement | 2026-06 | `packages/canonical-temporal-grid/src/grid.ts` |
| `🟢` | **Current** — enforces temporal metadata at the hardware level | 2026-08 | No dependencies |

### 3.10 `@aaes-os/cef-core` — CEF Core

| Phase | Event | Date | Evidence |
|-------|-------|------|----------|
| `🔵` | **Origin** — CEF v1.0 core — unified evidence schemas, Ajv validation, profile registry | 2026-06 | `packages/cef-core/src/index.ts` |
| `🟢` | **Current** — the core evidence framework for all AAES-OS surfaces | 2026-08 | 2 packages depend on it |

---

## 4. Simulation & Rendering Lineage

### 4.1 `@aaes-os/nova-substrate` — NovaCoda Rust Substrate

| Phase | Event | Date | Evidence |
|-------|-------|------|----------|
| `🔵` | **Origin** — Rust NovaCoda substrate exposing live socket protocol | 2026-06 | `packages/nova-substrate/src/` |
| `🟢` | **Current** — the Rust runtime surface for NovaCoda | 2026-08 | 1 package depends on it |

### 4.2 `@aaes-os/nova-substrate-client` — NovaCoda TS Client

| Phase | Event | Date | Evidence |
|-------|-------|------|----------|
| `🔵` | **Origin** — TypeScript client for NovaCoda Rust substrate | 2026-06 | `packages/nova-substrate-client/src/NovaCodaClient.ts` |
| `🟢` | **Current** — TypeScript interface to NovaCoda substrate | 2026-08 | 1 package depends on it |

### 4.3 `@aaes-os/nova-coda` — NovaCoda Runtime Facade

| Phase | Event | Date | Evidence |
|-------|-------|------|----------|
| `🔵` | **Origin** — runtime facade over Rust substrate and TS client | 2026-06 | `packages/nova-coda/src/index.ts` |
| `🟢` | **Current** — unified NovaCoda runtime surface | 2026-08 | 1 package depends on it |

### 4.4 `@aaes-os/nova-shell` — Nova Coding Shell

| Phase | Event | Date | Evidence |
|-------|-------|------|----------|
| `🔵` | **Origin** — Codex-style governed coding terminal | 2026-06 | `packages/nova-shell/src/NovaCodingShell.ts` |
| `🟢` | **Missions added** — MissionEngine, MissionState, MissionInvariant for task management | 2026-07 | `packages/nova-shell/src/missions/` |
| `🟢` | **GovernanceBridge added** — NovaGovernanceBridge for governance integration | 2026-07 | `packages/nova-shell/src/NovaGovernanceBridge.ts` |
| `🟢` | **RuntimeAdapter added** — NovaRuntimeAdapter for runtime integration | 2026-07 | `packages/nova-shell/src/NovaRuntimeAdapter.ts` |
| `🟢` | **Current** — powers `pnpm aais` CLI and aais-vscode extension | 2026-08 | 2 packages depend on it |

### 4.5 `@aaes-os/platform-mesh` — Platform Mesh

| Phase | Event | Date | Evidence |
|-------|-------|------|----------|
| `🔵` | **Origin** — multi-organism mesh networking | 2026-06 | `packages/platform-mesh/src/MeshNetwork.ts` |
| `🟢` | **Current** — governs cross-organism discovery and federation | 2026-08 | 1 package depends on it |

### 4.6 `@aaes-os/psom-mesh` — PSOM Mesh

| Phase | Event | Date | Evidence |
|-------|-------|------|----------|
| `🔵` | **Origin** — Planet-Scale Organism Mesh | 2026-06 | `packages/psom-mesh/src/PsomMesh.ts` |
| `🟢` | **Discovery, routing, governance, failover** — full mesh capabilities | 2026-07 | `packages/psom-mesh/src/discovery/`, `packages/psom-mesh/src/routing/` |
| `🟢` | **Current** — governs organism discovery, routing, and failover at scale | 2026-08 | 1 package depends on it |

---

## 5. Developer Tooling Lineage

### 5.1 `@aaes-os/coding-assistant` — CodingAssistant

| Phase | Event | Date | Evidence |
|-------|-------|------|----------|
| `🔵` | **Origin** — governed multi-backend coding assistant | 2026-06 | `packages/coding-assistant/src/CodingAssistant.ts` |
| `🔵` | **SovereignXOllamaBackend** — Ollama backend with SovereignX routing | 2026-06 | `packages/coding-assistant/src/SovereignXOllamaBackend.ts` |
| `🟢` | **createFreeCodingStack** — zero-cost setup with auto-discovery | 2026-07 | `packages/coding-assistant/src/createFreeCodingStack.ts` |
| `🟢` | **Model preference** — `--model qwen-3b/qwen-7b/groq/openrouter-free` CLI support | 2026-08 | `tools/aais-cli.ts` |
| `🟢` | **VS Code extension** — aais-vscode with chat UI, backend routing, governance toggle | 2026-08 | `packages/aais-vscode/` |
| `🟢` | **Current** — powers AAIS CLI, VS Code extension, and all coding operations | 2026-08 | 7 packages depend on it |

### 5.2 `@aaes-os/governed-runtime` — Governed Runtime

| Phase | Event | Date | Evidence |
|-------|-------|------|----------|
| `🔵` | **Origin** — universal coding adapter layer with CodingRouter | 2026-06 | `packages/governed-runtime/src/router/CodingRouter.ts` |
| `🔵` | **Backends** — OllamaBackend, OpenAiCompatibleBackend, GroqBackend, OpenRouterBackend, etc. | 2026-06 | `packages/governed-runtime/src/adapters/` |
| `🟢` | **Discovery** — discoverFreeBackends auto-detects available backends | 2026-07 | `packages/governed-runtime/src/discovery/discoverFreeBackends.ts` |
| `🟢` | **Policy engine** — YAML-based policy routing with preferredBackend governance | 2026-08 | `packages/governed-runtime/src/policies/` |
| `🟢` | **Current** — the adapter layer powering all coding backends | 2026-08 | 4 packages depend on it |

### 5.3 `@aaes-os/infinity-agents` — Infinity Coding Agent

| Phase | Event | Date | Evidence |
|-------|-------|------|----------|
| `🔵` | **Origin** — multi-step governed coding planner | 2026-06 | `packages/infinity-agents/src/InfinityCodingAgent.ts` |
| `🟢` | **Chain modules** — ConformanceGate, CorpusAdmitter, EGL1Checker, EvidenceBundleCollector, ReplayVerifier | 2026-07 | `packages/infinity-agents/src/chain/` |
| `🟢` | **Orchestration** — AgentScheduler, OrchestrationEngine, OrchestrationInvariant | 2026-07 | `packages/infinity-agents/src/orchestration/` |
| `🟢` | **Current** — multi-step agentic coding with full evidence chain | 2026-08 | 1 package depends on it |

### 5.4 `@aaes-os/sandbox` — Governed Sandbox

| Phase | Event | Date | Evidence |
|-------|-------|------|----------|
| `🔵` | **Origin** — governed code-execution sandbox with module allowlisting | 2026-06 | `packages/sandbox/src/GovernedSandbox.ts` |
| `🟢` | **Current** — provides sandboxed execution for all coding operations | 2026-08 | 1 package depends on it |

### 5.5 `@aaes-os/sovereignx-router` — SovereignX Router

| Phase | Event | Date | Evidence |
|-------|-------|------|----------|
| `🔵` | **Origin** — CPU governance over GPU acceleration with CIEMS-style limits | 2026-06 | `packages/sovereignx-router/src/SovereignXRouter.ts` |
| `🟢` | **Hardware governor** — GPU/CPU routing based on thermals, VRAM, utilization | 2026-07 | `packages/sovereignx-router/src/hardwareGovernor.ts` |
| `🟢` | **Cluster routing** — multi-node cluster routing with failover | 2026-07 | `packages/sovereignx-router/src/clusterRouting.ts` |
| `🟢` | **Render bridge** — cross-backend rendering bridge | 2026-07 | `packages/sovereignx-router/src/renderBridge.ts` |
| `🟢` | **Current** — governs hardware-aware routing for all compute operations | 2026-08 | 2 packages depend on it |

### 5.6 `@aaes-os/platform-cli` — Platform CLI

| Phase | Event | Date | Evidence |
|-------|-------|------|----------|
| `🔵` | **Origin** — unified command-line interface for the AAES super-platform | 2026-06 | `packages/platform-cli/src/cli.ts` |
| `🟢` | **LIRL intent** — lirlIntent command for LIRL integration | 2026-07 | `packages/platform-cli/src/lirlIntent.ts` |
| `🟢` | **Current** — CLI entrypoint for platform operations | 2026-08 | 3 packages depend on it |

### 5.7 `@aaes-os/platform-sdk` — Platform SDK

| Phase | Event | Date | Evidence |
|-------|-------|------|----------|
| `🔵` | **Origin** — official TypeScript/JavaScript SDK for PSOM + SGCE | 2026-06 | `packages/platform-sdk/src/PlatformClient.ts` |
| `🟢` | **LocalPlatform** — local platform client for development | 2026-07 | `packages/platform-sdk/src/LocalPlatform.ts` |
| `🟢` | **Current** — SDK for building on the AAES super-platform | 2026-08 | 1 package depends on it |

### 5.8 `@aaes-os/aais-vscode` — AAIS VS Code Extension

| Phase | Event | Date | Evidence |
|-------|-------|------|----------|
| `🟡` | **Origin** — VS Code extension skeleton with chat UI, backend routing, governance toggle | 2026-08 | `packages/aais-vscode/` |
| `🟡` | **Current** — partial; needs streaming, context management, full test coverage | 2026-08 | 3 packages depend on it |

### 5.9 `@aaes-os/architect-agent` — Architect Agent

| Phase | Event | Date | Evidence |
|-------|-------|------|----------|
| `🟡` | **Origin** — governed local coding agent with Ollama model support | 2026-06 | `packages/architect-agent/src/architectAgent.ts` |
| `🟡` | **Current** — partial; needs full governance integration | 2026-08 | No dependencies |

### 5.10 `@aaes-os/cef-certification` — CEF Certification

| Phase | Event | Date | Evidence |
|-------|-------|------|----------|
| `🟡` | **Origin** — CEF Certification Engine stub | 2026-06 | `packages/cef-certification/src/index.ts` |
| `🟡` | **Current** — stub, promotion gated by cef-core | 2026-08 | 1 package depends on it |

---

## 6. Products Lineage

### 6.1 `@aaes-os/platform-core` — Platform Core

| Phase | Event | Date | Evidence |
|-------|-------|------|----------|
| `🔵` | **Origin** — super-platform core with governance profiles, capability versioning, billing, API keys | 2026-06 | `packages/platform-core/src/PlatformService.ts` |
| `🟢` | **Auth** — apiKeys, customers, organizations for platform authentication | 2026-07 | `packages/platform-core/src/auth/` |
| `🟢` | **Billing** — meter, treasury, usage for platform billing | 2026-07 | `packages/platform-core/src/billing/` |
| `🟢` | **Versioning** — semver, registry for capability versioning | 2026-07 | `packages/platform-core/src/versioning/` |
| `🟢` | **Audit** — signing, validator, schema for platform audit | 2026-07 | `packages/platform-core/src/audit/` |
| `🟢` | **Current** — the core product platform for AAES-OS | 2026-08 | 4 packages depend on it |

### 6.2 `@aaes-os/sgce` — Self-Governing Capability Economy

| Phase | Event | Date | Evidence |
|-------|-------|------|----------|
| `🔵` | **Origin** — tokenization, marketplace, provenance, and lifecycle | 2026-06 | `packages/sgce/src/SgceEconomy.ts` |
| `🟢` | **Lifecycle** — capability lifecycle management | 2026-07 | `packages/sgce/src/lifecycle/lifecycle.ts` |
| `🟢` | **Marketplace** — capability marketplace | 2026-07 | `packages/sgce/src/marketplace/marketplace.ts` |
| `🟢` | **Pricing** — capability pricing | 2026-07 | `packages/sgce/src/pricing/pricing.ts` |
| `🟢` | **Provenance** — capability provenance and lineage | 2026-07 | `packages/sgce/src/provenance/lineage.ts` |
| `🟢` | **Tokenization** — capability tokenization | 2026-07 | `packages/sgce/src/tokens/tokenization.ts` |
| `🟢` | **Current** — the capability economy for AAES-OS | 2026-08 | 1 package depends on it |

### 6.3 `@aaes-os/coda-doc` — Coda Document Catalog

| Phase | Event | Date | Evidence |
|-------|-------|------|----------|
| `🔵` | **Origin** — canonical Coda document catalog | 2026-06 | `packages/coda-doc/src/index.ts` |
| `🟢` | **Current** — catalogs all Coda documents for the platform | 2026-08 | No dependencies |

### 6.4 `@aaes-os/coda-runtime` — Coda Runtime

| Phase | Event | Date | Evidence |
|-------|-------|------|----------|
| `🔵` | **Origin** — runtime facade for the Coda stack over NovaCoda | 2026-06 | `packages/coda-runtime/src/index.ts` |
| `🟢` | **Current** — governs Coda runtime execution | 2026-08 | 2 packages depend on it |

### 6.5 `@aaes-os/operator-surface` — Operator Surface

| Phase | Event | Date | Evidence |
|-------|-------|------|----------|
| `🟡` | **Origin** — operator surface for the AAES super-platform | 2026-06 | `packages/operator-surface/` |
| `🟡` | **Current** — partial, needs full operator surface implementation | 2026-08 | No dependencies |

---

## 7. Operations Lineage

### 7.1 `@aaes-os/ops-console` — Ops Console

| Phase | Event | Date | Evidence |
|-------|-------|------|----------|
| `🔵` | **Origin** — React UI + Express telemetry + Prometheus /metrics | 2026-06 | `services/ops-console/src/App.test.tsx` |
| `🟢` | **Telemetry** — hardware telemetry and governor state | 2026-07 | `services/ops-console/src/server.test.ts` |
| `🟢` | **Current** — the operations console for AAES-OS | 2026-08 | No @aaes-os dependencies |

### 7.2 `@aaes-os/image-studio` — Image Studio

| Phase | Event | Date | Evidence |
|-------|-------|------|----------|
| `🔵` | **Origin** — AAIS-governed image studio with Pollinations (keyless) and Gemini | 2026-06 | `packages/image-studio/src/` |
| `🟢` | **Providers** — Genblaze, Storyforge, Cloudflare, HuggingFace, hfspace | 2026-07 | `packages/image-studio/src/providers/` |
| `🟢` | **CLI + Web UI** — both CLI and local web interface | 2026-07 | `packages/image-studio/src/cli.ts`, `packages/image-studio/src/server.ts` |
| `🟢` | **Current** — governs image generation for AAIS | 2026-08 | 1 package depends on it |

### 7.3 `@aaes-os/cef-stewardship` — CEF Stewardship

| Phase | Event | Date | Evidence |
|-------|-------|------|----------|
| `🟡` | **Origin** — CEF Stewardship stub for certificate lifecycle | 2026-06 | `packages/cef-stewardship/src/index.ts` |
| `🟡` | **Current** — stub, needs full certificate lifecycle implementation | 2026-08 | 2 packages depend on it |

### 7.4 `@aaes-os/omega-stress-harness` — Omega Stress Harness

| Phase | Event | Date | Evidence |
|-------|-------|------|----------|
| `🔵` | **Origin** — stress harness for constitutional enforcement | 2026-06 | `packages/omega-stress-harness/src/omegaStressHarness.ts` |
| `🟢` | **Current** — governs stress testing for constitutional enforcement | 2026-08 | 2 packages depend on it |

### 7.5 `@aaes-os/transition-validation-pipeline` — TVP

| Phase | Event | Date | Evidence |
|-------|-------|------|----------|
| `🔵` | **Origin** — transition validation pipeline for constitutional enforcement | 2026-06 | `packages/transition-validation-pipeline/src/transitionValidationPipeline.ts` |
| `🟢` | **Current** — governs transition validation for constitutional enforcement | 2026-08 | 1 package depends on it |

### 7.6 `@aaes-os/ceip-runtime` — CEIP Runtime

| Phase | Event | Date | Evidence |
|-------|-------|------|----------|
| `🔵` | **Origin** — conformance, contracts, freeze, governance artifacts | 2026-06 | `packages/ceip-runtime/src/index.ts` |
| `🟢` | **Current** — governs CEIP conformance checks | 2026-08 | No dependencies |

---

## Cross-Reference Map

| Capability | Atlas Location | Lineage Location |
|------------|---------------|-----------------|
| Governance Kernel | [Atlas §1](../atlas/README.md#1-governance-kernel) | [Lineage §1](#1-governance-kernel-lineage) |
| Runtime Services | [Atlas §2](../atlas/README.md#2-runtime-services) | [Lineage §2](#2-runtime-services-lineage) |
| Evidence & Provenance | [Atlas §3](../atlas/README.md#3-evidence--provenance) | [Lineage §3](#3-evidence--provenance-lineage) |
| Simulation & Rendering | [Atlas §4](../atlas/README.md#4-simulation--rendering) | [Lineage §4](#4-simulation--rendering-lineage) |
| Developer Tooling | [Atlas §5](../atlas/README.md#5-developer-tooling) | [Lineage §5](#5-developer-tooling-lineage) |
| Products | [Atlas §6](../atlas/README.md#6-products) | [Lineage §6](#6-products-lineage) |
| Operations | [Atlas §7](../atlas/README.md#7-operations) | [Lineage §7](#7-operations-lineage) |

---

*Last updated: 2026-08-02. Cross-references the Architectural Atlas at `docs/atlas/README.md`.*
