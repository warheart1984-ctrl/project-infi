# Architect Agent Loop Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the missing architect-agent layer as a concrete AAES-OS package with UGR -> UCR contract derivation, ALA runtimes, deterministic reversible mutation envelopes, EGL-1 replay equivalence, evidence receipts, and tests.

**Status:** Complete. Package build, workspace tests, and CTS verified on 2026-06-30.

**Architecture:** Add `packages/architect-agent` as a pure TypeScript package over the existing green AAES-OS workspace. The package exposes one orchestrator, `ArchitectAgentLoop`, and focused primitives for contracts, runtimes, envelopes, safety, and EGL-1 equivalence. No files are mutated by this package; it emits governed patch envelopes that Codex or another execution substrate can apply.

**Tech Stack:** TypeScript ESM, Vitest, Node `crypto`, existing `@aaes-os/evidence-receipts`.

---

### Task 1: Package Scaffold And Red Contract Test

**Files:**
- Create: `packages/architect-agent/package.json`
- Create: `packages/architect-agent/tsconfig.json`
- Create: `packages/architect-agent/vitest.config.ts`
- Create: `packages/architect-agent/src/index.ts`
- Create: `packages/architect-agent/src/architectAgent.test.ts`
- Modify: `tsconfig.base.json`
- Modify: `vitest.config.ts`

- [ ] **Step 1: Write the failing test**

Create `packages/architect-agent/src/architectAgent.test.ts` with imports from `./index.js` and a test named `derives a CMC from UGC closure invariants`.

- [ ] **Step 2: Run test to verify it fails**

Run: `.\node_modules\.bin\vitest.CMD run packages\architect-agent\src\architectAgent.test.ts`
Expected: FAIL because `packages/architect-agent/src/index.ts` exports do not exist yet.

- [ ] **Step 3: Add package scaffold and minimal bridge exports**

Create package files and implement `createDefaultUnifiedGovernanceContract` plus `UGRUCRBridge.issueCognitiveModeContract`.

- [ ] **Step 4: Run test to verify it passes**

Run: `.\node_modules\.bin\vitest.CMD run packages\architect-agent\src\architectAgent.test.ts`
Expected: PASS for the CMC derivation test.

### Task 2: Runtime Family Red Tests

**Files:**
- Modify: `packages/architect-agent/src/architectAgent.test.ts`
- Modify: `packages/architect-agent/src/index.ts`

- [ ] **Step 1: Write failing tests**

Add tests proving `ArchitectRuntime`, `BuilderRuntime`, `IntegrationRuntime`, and `SafetyRuntime` execute under a derived `CognitiveModeContract`.

- [ ] **Step 2: Run test to verify it fails**

Run: `.\node_modules\.bin\vitest.CMD run packages\architect-agent\src\architectAgent.test.ts`
Expected: FAIL because runtime classes are not implemented.

- [ ] **Step 3: Implement minimal runtime family**

Implement deterministic runtime classes with no hidden state and no filesystem mutation.

- [ ] **Step 4: Run test to verify it passes**

Run: `.\node_modules\.bin\vitest.CMD run packages\architect-agent\src\architectAgent.test.ts`
Expected: PASS.

### Task 3: Deterministic Envelope And EGL-1 Tests

**Files:**
- Modify: `packages/architect-agent/src/architectAgent.test.ts`
- Modify: `packages/architect-agent/src/index.ts`

- [ ] **Step 1: Write failing tests**

Add tests proving identical build inputs produce identical envelope IDs, changed `pre_state_hash` changes envelope IDs, each patch has a reverse patch, and EGL-1 replay equivalence rejects altered envelopes.

- [ ] **Step 2: Run test to verify it fails**

Run: `.\node_modules\.bin\vitest.CMD run packages\architect-agent\src\architectAgent.test.ts`
Expected: FAIL because envelope determinism and EGL-1 are not implemented.

- [ ] **Step 3: Implement deterministic envelopes and EGL-1**

Implement stable JSON hashing, reversible patch normalization, `IntegrationRuntime.wrapBuildPlan`, and `evaluateEgl1ReplayEquivalence`.

- [ ] **Step 4: Run test to verify it passes**

Run: `.\node_modules\.bin\vitest.CMD run packages\architect-agent\src\architectAgent.test.ts`
Expected: PASS.

### Task 4: Automatic ArchitectAgentLoop Test

**Files:**
- Modify: `packages/architect-agent/src/architectAgent.test.ts`
- Modify: `packages/architect-agent/src/index.ts`

- [ ] **Step 1: Write failing test**

Add a test proving `ArchitectAgentLoop.execute()` returns a governed act with CMC, architecture plan, build plan, deterministic envelopes, safety approval, EGL-1 approval, and an evidence receipt.

- [ ] **Step 2: Run test to verify it fails**

Run: `.\node_modules\.bin\vitest.CMD run packages\architect-agent\src\architectAgent.test.ts`
Expected: FAIL because orchestrator is missing.

- [ ] **Step 3: Implement orchestrator**

Implement `ArchitectAgentLoop` using bridge -> ArchitectRuntime -> BuilderRuntime -> IntegrationRuntime -> SafetyRuntime -> evidence receipt.

- [ ] **Step 4: Run test to verify it passes**

Run: `.\node_modules\.bin\vitest.CMD run packages\architect-agent\src\architectAgent.test.ts`
Expected: PASS.

### Task 5: Workspace Verification

**Files:**
- Modify: `tsconfig.base.json`
- Modify: `vitest.config.ts`

- [ ] **Step 1: Run package build**

Run: `corepack pnpm --filter @aaes-os/architect-agent run build`
Expected: PASS.

- [ ] **Step 2: Run full workspace build**

Run: `corepack pnpm -r run build`
Expected: PASS.

- [ ] **Step 3: Run full test suite**

Run: `.\node_modules\.bin\vitest.CMD run`
Expected: PASS.
