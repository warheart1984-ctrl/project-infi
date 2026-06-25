# AAES OS MRI Operator Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an AAES OS-only MRI v0.1 operator pilot with testable instrument logic and an ops-console readout.

**Architecture:** Add `@aaes-os/mri-instrument` as a pure TypeScript workspace package. Wire the AAES OS ops console to expose a deterministic `/mri` endpoint and render the seeded before/after assessment.

**Tech Stack:** TypeScript, pnpm workspaces, Vitest, Express, React.

---

### Task 1: MRI Instrument Package

**Files:**
- Create: `aaes-os/packages/mri-instrument/package.json`
- Create: `aaes-os/packages/mri-instrument/tsconfig.json`
- Create: `aaes-os/packages/mri-instrument/vitest.config.ts`
- Create: `aaes-os/packages/mri-instrument/src/index.ts`
- Create: `aaes-os/packages/mri-instrument/src/mriInstrument.test.ts`

- [ ] **Step 1: Write failing tests**

Cover continuity scoring, confidence, delta state, risk detection, intervention ranking, and report generation in `src/mriInstrument.test.ts`.

- [ ] **Step 2: Run tests to verify RED**

Run: `pnpm --filter @aaes-os/mri-instrument test`

Expected: package is missing or tests fail because exported functions do not exist.

- [ ] **Step 3: Implement package and formulas**

Implement types plus pure functions: `computeContinuityComponents`, `continuityScore`, `governanceScore`, `memoryScore`, `computeConfidence`, `computeDeltaState`, `detectRisks`, `recommendInterventions`, `runMRI`, `runMRIComparison`, and `generateBeforeAfterReport`.

- [ ] **Step 4: Run tests to verify GREEN**

Run: `pnpm --filter @aaes-os/mri-instrument test`

Expected: all MRI package tests pass.

### Task 2: Workspace Wiring

**Files:**
- Modify: `aaes-os/tsconfig.base.json`
- Modify: `aaes-os/vitest.config.ts`
- Modify: `aaes-os/services/ops-console/package.json`
- Modify: `aaes-os/services/ops-console/tsconfig.json`
- Modify: `aaes-os/services/ops-console/vite.config.ts`
- Modify: `aaes-os/services/ops-console/vitest.config.ts`

- [ ] **Step 1: Add workspace aliases and dependency**

Add `@aaes-os/mri-instrument` path aliases and make ops-console depend on the new workspace package.

- [ ] **Step 2: Run TypeScript build for package graph**

Run: `pnpm -r run build`

Expected: the workspace builds or reports only issues introduced by wiring, which must be fixed before continuing.

### Task 3: Ops Console Endpoint

**Files:**
- Create: `aaes-os/services/ops-console/src/mriState.ts`
- Modify: `aaes-os/services/ops-console/src/server.ts`
- Modify: `aaes-os/services/ops-console/src/server.test.ts`

- [ ] **Step 1: Write failing endpoint test**

Assert `GET /mri` returns `before`, `after`, `deltaState`, `interventions`, and `report`.

- [ ] **Step 2: Run test to verify RED**

Run: `pnpm --filter @aaes-os/ops-console test -- src/server.test.ts`

Expected: `GET /mri` returns 404 before implementation.

- [ ] **Step 3: Implement seeded MRI state and endpoint**

Create deterministic before/after input data in `mriState.ts`, call `runMRIComparison`, and return it from `GET /mri`.

- [ ] **Step 4: Run endpoint test to verify GREEN**

Run: `pnpm --filter @aaes-os/ops-console test -- src/server.test.ts`

Expected: endpoint tests pass.

### Task 4: Operator Readout

**Files:**
- Modify: `aaes-os/services/ops-console/src/App.tsx`
- Modify: `aaes-os/services/ops-console/vite.config.ts`

- [ ] **Step 1: Render MRI readout**

Fetch `/mri`, then render continuity, governance, memory, confidence, state delta, top risks, top interventions, and report summary.

- [ ] **Step 2: Build ops console**

Run: `pnpm --filter @aaes-os/ops-console build`

Expected: TypeScript build passes.

### Task 5: Final Verification

**Files:**
- All AAES OS files touched above.

- [ ] **Step 1: Run package test**

Run: `pnpm --filter @aaes-os/mri-instrument test`

Expected: all tests pass.

- [ ] **Step 2: Run ops-console tests**

Run: `pnpm --filter @aaes-os/ops-console test`

Expected: all tests pass.

- [ ] **Step 3: Run full AAES OS test command if workspace state allows**

Run: `pnpm test`

Expected: the workspace test command passes, or any unrelated pre-existing failures are reported with evidence.

## Self Review

The plan keeps all changes under `aaes-os`, implements the approved end-to-end pilot slice, and includes tests before production implementation. It excludes project-level frontend routing and backend persistence as intended.
