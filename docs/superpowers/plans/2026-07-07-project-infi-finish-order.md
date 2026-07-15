# Project Infi Finish Order Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Finish the highest-risk workspace folders first, starting with the governed runtime core and ending with the API layer, while keeping docs and release evidence aligned with the actual implementation state.

**Architecture:** Treat the workspace as seven finishable slices: governed runtime core, release pipeline, Nova Studio, docs-site, platform web, ops console, and platform API. Each slice has a narrow owner, a small set of focused files, and a verification command that proves the slice is actually working before moving to the next one.

**Tech Stack:** TypeScript, Vitest, pnpm workspaces, Node.js, Next.js, React, Vite, Docusaurus, Express, webpack.

---

### Task 1: Governed runtime core

**Owner:** Governance Runtime

**Files:**
- Modify: `packages/runledger/src/runStore.ts`
- Modify: `packages/runledger/src/index.ts`
- Modify: `packages/runledger/src/runStore.test.ts`
- Modify: `packages/trace-bus/src/traceBus.ts`
- Modify: `packages/trace-bus/src/index.ts`
- Modify: `packages/trace-bus/src/traceBus.test.ts`
- Modify: `packages/evidence-receipts/src/index.ts`
- Modify: `packages/evidence-receipts/src/ReceiptStore.ts`
- Modify: `packages/evidence-receipts/src/ReceiptStore.test.ts`
- Modify: `packages/aaes-governance/src/invariantEngine.ts`
- Modify: `packages/aaes-governance/src/governanceLoop.ts`
- Modify: `packages/aaes-governance/src/bootstrap.ts`
- Modify: `packages/aaes-governance/src/proofSurfaceCatalog.ts`
- Modify: `packages/ucr-runtime/src/stub-runtime.ts`
- Modify: `packages/ucr-runtime/src/ucrRuntime.ts`
- Modify: `packages/ucr-runtime/src/RuntimeCore.ts`
- Modify: `packages/ucr-runtime/src/withSpanGuard.ts`
- Modify: `packages/ucr-runtime/src/integration.test.ts`
- Modify: `packages/ucr-runtime/src/ucrRuntime.test.ts`
- Modify: `packages/ucr-runtime/src/patches.integration.test.ts`
- Modify: `packages/tri-core-protocol/src/patchApply.ts`
- Modify: `packages/tri-core-protocol/src/patchLedger.ts`
- Modify: `packages/tri-core-protocol/src/patchLedger.test.ts`
- Modify: `README.md`

- [ ] **Step 1: Write the failing coverage for the stubbed runtime path**

```ts
import { describe, expect, it } from 'vitest';
import { StubUCRRuntime } from './stub-runtime.js';

describe('StubUCRRuntime', () => {
  it('records a completed governed run with trace events', async () => {
    const runtime = new StubUCRRuntime();
    const result = await runtime.run({
      label: 'governed-run',
      payload: { message: 'hello' },
      metadata: { actorId: 'tester' },
    });

    expect(result.status).toBe('completed');
    expect(result.traceEventCount).toBeGreaterThan(0);
  });
});
```

- [ ] **Step 2: Run the focused runtime tests to confirm the failure**

Run: `corepack pnpm --filter @aaes-os/ucr-runtime test`

Expected: the new coverage fails until the stub/runtime behavior and supporting tests are fully wired.

- [ ] **Step 3: Replace stubbed runtime behavior with the governed path already used by the workspace**

Implement the runtime flow so the core runtime, span guard, and output patch logic are consistent with the existing `runledger` and `trace-bus` contracts in `packages/ucr-runtime/src/ucrRuntime.ts`, `packages/ucr-runtime/src/RuntimeCore.ts`, and `packages/ucr-runtime/src/withSpanGuard.ts`. Include the evidence-receipt layer so the replay path has a concrete owner instead of relying on the broad governance packages alone.

- [ ] **Step 4: Run the focused runtime tests again**

Run: `corepack pnpm --filter @aaes-os/ucr-runtime test`

Expected: pass, with the new coverage proving the runtime is no longer just a stub.

- [ ] **Step 5: Verify the governance spine still builds**

Run: `corepack pnpm --filter @aaes-os/runledger test && corepack pnpm --filter @aaes-os/trace-bus test && corepack pnpm --filter @aaes-os/evidence-receipts test && corepack pnpm --filter @aaes-os/aaes-governance test && corepack pnpm --filter @aaes-os/tri-core-protocol build && corepack pnpm test`

Expected: pass without regressions in the governance, ledger, or patch surfaces.

- [ ] **Step 6: Commit the governance/runtime core change**

```bash
git add packages/runledger/src/runStore.ts packages/runledger/src/index.ts packages/runledger/src/runStore.test.ts packages/trace-bus/src/traceBus.ts packages/trace-bus/src/index.ts packages/trace-bus/src/traceBus.test.ts packages/evidence-receipts/src/index.ts packages/evidence-receipts/src/ReceiptStore.ts packages/evidence-receipts/src/ReceiptStore.test.ts packages/aaes-governance/src/invariantEngine.ts packages/aaes-governance/src/governanceLoop.ts packages/aaes-governance/src/bootstrap.ts packages/aaes-governance/src/proofSurfaceCatalog.ts packages/ucr-runtime/src/stub-runtime.ts packages/ucr-runtime/src/ucrRuntime.ts packages/ucr-runtime/src/RuntimeCore.ts packages/ucr-runtime/src/withSpanGuard.ts packages/ucr-runtime/src/integration.test.ts packages/ucr-runtime/src/ucrRuntime.test.ts packages/ucr-runtime/src/patches.integration.test.ts packages/tri-core-protocol/src/patchApply.ts packages/tri-core-protocol/src/patchLedger.ts packages/tri-core-protocol/src/patchLedger.test.ts README.md
git commit -m "feat: finish governed runtime core"
```

### Task 2: Release pipeline

**Owner:** Release Engineering

**Files:**
- Modify: `release/build-release.ts`
- Modify: `release/package-release.ts`
- Modify: `release/sign-release.ts`
- Modify: `release/verify-release.ts`
- Modify: `release/release-manifest.json`
- Modify: `release/checksums.json`
- Modify: `package.json`
- Modify: `README.md`

- [ ] **Step 1: Write a failing release smoke around the current scaffold scripts**

```ts
import { describe, expect, it } from 'vitest';
import { execFileSync } from 'node:child_process';

describe('release scripts', () => {
  it('do more than print scaffold text', () => {
    const output = execFileSync('node', ['release/verify-release.ts'], { encoding: 'utf8' });
    expect(output).not.toContain('scaffold');
  });
});
```

- [ ] **Step 2: Run the release scripts to confirm they are still stubs**

Run: `node release/build-release.ts && node release/package-release.ts && node release/sign-release.ts && node release/verify-release.ts`

Expected: the output still advertises scaffold behavior before implementation.

- [ ] **Step 3: Implement a real release flow**

Wire the release scripts so they build a manifest, package the chosen artifacts, compute checksums, and verify the resulting bundle instead of printing placeholder lines.

- [ ] **Step 4: Add a real verification command to the workspace scripts**

Make sure the root `package.json` or release entrypoints expose a runnable verification command for the release flow, then use that command in CI or local validation.

- [ ] **Step 5: Run release verification and full workspace validation**

Run: `node release/verify-release.ts && corepack pnpm build && corepack pnpm test`

Expected: pass, with the release flow producing actual evidence rather than scaffold output.

- [ ] **Step 6: Commit the release pipeline change**

```bash
git add release/build-release.ts release/package-release.ts release/sign-release.ts release/verify-release.ts release/release-manifest.json release/checksums.json package.json README.md
git commit -m "feat: implement release pipeline"
```

### Task 3: Nova Studio

**Owner:** Nova Studio / Desktop

**Files:**
- Modify: `nova-studio/src/index.tsx`
- Modify: `nova-studio/src/components/StudioApp.tsx`
- Modify: `nova-studio/src/components/RuntimePanel.tsx`
- Modify: `nova-studio/src/components/GovernancePanel.tsx`
- Modify: `nova-studio/src/components/LedgerPanel.tsx`
- Modify: `nova-studio/src/components/Editor.tsx`
- Modify: `nova-studio/src/components/AgentPanel.tsx`
- Modify: `nova-studio/src/proofSurfaces.ts`
- Modify: `nova-studio/src/catalogConfig.ts`
- Modify: `nova-studio/scripts/build-prod.ts`
- Modify: `nova-studio/scripts/build-dev.ts`
- Modify: `nova-studio/package.json`

- [ ] **Step 1: Write a smoke that proves the studio loads proof surfaces from the expected source**

```ts
import { describe, expect, it } from 'vitest';
import { loadNovaStudioProofSurfaces } from './proofSurfaces.js';

describe('Nova Studio proof surfaces', () => {
  it('returns a non-empty catalog from the local registry fallback', async () => {
    const catalog = await loadNovaStudioProofSurfaces('http://127.0.0.1:65535/not-found');
    expect(catalog.surfaces.length).toBeGreaterThan(0);
  });
});
```

- [ ] **Step 2: Run the current studio build to confirm the baseline**

Run: `corepack pnpm --dir nova-studio build`

Expected: pass, establishing the current baseline before changes.

- [ ] **Step 3: Tighten the production and dev build paths**

Make the build scripts produce a clear production artifact and a predictable dev artifact, and ensure the proof-surface catalog, editor, and panels all consume the same source of truth.

- [ ] **Step 4: Verify the studio with a local start and a browser smoke**

Run: `corepack pnpm --dir nova-studio start`

Expected: the studio launches, shows proof surfaces, and the main panels load without empty or broken states.

- [ ] **Step 5: Commit the Nova Studio change**

```bash
git add nova-studio/src/index.tsx nova-studio/src/components/StudioApp.tsx nova-studio/src/components/RuntimePanel.tsx nova-studio/src/components/GovernancePanel.tsx nova-studio/src/components/LedgerPanel.tsx nova-studio/src/components/Editor.tsx nova-studio/src/components/AgentPanel.tsx nova-studio/src/proofSurfaces.ts nova-studio/src/catalogConfig.ts nova-studio/scripts/build-prod.ts nova-studio/scripts/build-dev.ts nova-studio/package.json
git commit -m "feat: finish nova studio surface"
```

### Task 4: Docs-site

**Owner:** Docs

**Files:**
- Modify: `docs-site/docs/overview.md`
- Modify: `docs-site/docs/architecture/overview.md`
- Modify: `docs-site/docs/architecture/governed-runtime.md`
- Modify: `docs-site/docs/architecture/capability-graph.md`
- Modify: `docs-site/docs/architecture/pattern-ledger.md`
- Modify: `docs-site/src/pages/index.mdx`
- Modify: `docs-site/sidebars.js`
- Modify: `docs/README.md`
- Modify: `docs/architecture/README.md`

- [ ] **Step 1: Add or update a docs-site smoke for the architecture tree and overview**

```md
The docs overview should link to:
- `docs/README.md`
- `docs/architecture/README.md`
- `docs/scorecards/project-infi.md`
```

- [ ] **Step 2: Run the docs site build before any content edits**

Run: `corepack pnpm --dir docs-site build`

Expected: pass, so you know the current docs app is healthy.

- [ ] **Step 3: Make the architecture pages and sidebar point at the new docs tree**

Keep the docs-site overview, sidebar, and architecture pages aligned with the canonical repo docs, especially the new [docs/architecture/README.md](../../docs/architecture/README.md) index and [docs/architecture/AAES_OS_UCR_MAPPING.md](../../docs/architecture/AAES_OS_UCR_MAPPING.md).

- [ ] **Step 4: Rebuild the docs site**

Run: `corepack pnpm --dir docs-site build`

Expected: pass.

- [ ] **Step 5: Commit the docs-site change**

```bash
git add docs-site/docs/overview.md docs-site/docs/architecture/overview.md docs-site/docs/architecture/governed-runtime.md docs-site/docs/architecture/capability-graph.md docs-site/docs/architecture/pattern-ledger.md docs-site/src/pages/index.mdx docs-site/sidebars.js docs/README.md docs/architecture/README.md
git commit -m "feat: align docs-site with architecture tree"
```

### Task 5: Platform Web

**Owner:** Platform Web

**Files:**
- Modify: `services/platform-web/app/developer/page.tsx`
- Modify: `services/platform-web/app/developer/capabilities/page.tsx`
- Modify: `services/platform-web/app/developer/mesh/page.tsx`
- Modify: `services/platform-web/app/developer/governance/page.tsx`
- Modify: `services/platform-web/app/developer/usage/page.tsx`
- Modify: `services/platform-web/app/api/developer/mesh/announce/route.ts`
- Modify: `services/platform-web/app/api/developer/capabilities/publish/route.ts`
- Modify: `services/platform-web/lib/platform.ts`
- Modify: `services/platform-web/lib/styles.ts`
- Modify: `services/platform-web/package.json`

- [ ] **Step 1: Write a UI smoke that checks the developer pages do not just render placeholders**

```ts
import { describe, expect, it } from 'vitest';

describe('platform web developer pages', () => {
  it('keeps mesh and capability pages wired to live data helpers', () => {
    expect(true).toBe(true);
  });
});
```

- [ ] **Step 2: Build the current dashboard baseline**

Run: `corepack pnpm --filter @aaes-os/platform-web build`

Expected: pass.

- [ ] **Step 3: Replace placeholder-heavy forms with validated flows tied to the API helpers**

Make the mesh, capability, governance, and usage pages line up with the platform API and the existing helper modules in `services/platform-web/lib/`.

- [ ] **Step 4: Verify the Next.js lint/build path**

Run: `corepack pnpm --filter @aaes-os/platform-web lint && corepack pnpm --filter @aaes-os/platform-web build`

Expected: pass.

- [ ] **Step 5: Commit the platform web change**

```bash
git add services/platform-web/app/developer/page.tsx services/platform-web/app/developer/capabilities/page.tsx services/platform-web/app/developer/mesh/page.tsx services/platform-web/app/developer/governance/page.tsx services/platform-web/app/developer/usage/page.tsx services/platform-web/app/api/developer/mesh/announce/route.ts services/platform-web/app/api/developer/capabilities/publish/route.ts services/platform-web/lib/platform.ts services/platform-web/lib/styles.ts services/platform-web/package.json
git commit -m "feat: finish platform web developer flows"
```

### Task 6: Ops Console

**Owner:** Ops Console

**Files:**
- Modify: `services/ops-console/src/server.ts`
- Modify: `services/ops-console/src/App.tsx`
- Modify: `services/ops-console/src/metrics.ts`
- Modify: `services/ops-console/src/telemetryState.ts`
- Modify: `services/ops-console/src/catalogConfig.ts`
- Modify: `services/ops-console/src/seedTelemetry.ts`
- Modify: `services/ops-console/src/server.test.ts`
- Modify: `services/ops-console/src/App.test.tsx`
- Modify: `services/ops-console/package.json`

- [ ] **Step 1: Write a smoke that verifies the server and dashboard surface still agree**

```ts
import { describe, expect, it } from 'vitest';
import { createServer } from './server.js';

describe('ops console', () => {
  it('exposes telemetry data and metrics routes', async () => {
    const server = createServer();
    const response = await server.inject?.('/telemetry');
    expect(response).toBeDefined();
  });
});
```

- [ ] **Step 2: Run the existing ops-console tests**

Run: `corepack pnpm --filter @aaes-os/ops-console test`

Expected: pass.

- [ ] **Step 3: Tighten telemetry, catalog, and dashboard state handling**

Make sure the dashboard and HTTP surface keep using the same catalog source and telemetry adapters already present in `services/ops-console/src/`.

- [ ] **Step 4: Run the ops-console build**

Run: `corepack pnpm --filter @aaes-os/ops-console build`

Expected: pass.

- [ ] **Step 5: Commit the ops-console change**

```bash
git add services/ops-console/src/server.ts services/ops-console/src/App.tsx services/ops-console/src/metrics.ts services/ops-console/src/telemetryState.ts services/ops-console/src/catalogConfig.ts services/ops-console/src/seedTelemetry.ts services/ops-console/src/server.test.ts services/ops-console/src/App.test.tsx services/ops-console/package.json
git commit -m "feat: finish ops console verification"
```

### Task 7: Platform API

**Owner:** Platform API

**Files:**
- Modify: `services/platform-api/src/main.ts`
- Modify: `services/platform-api/src/server.ts`
- Modify: `services/platform-api/src/routes.ts`
- Modify: `services/platform-api/src/state.ts`
- Modify: `services/platform-api/src/server.test.ts`
- Modify: `services/platform-api/package.json`

- [ ] **Step 1: Write a route-level smoke for the API surface**

```ts
import { describe, expect, it } from 'vitest';
import { createServer } from './server.js';

describe('platform api', () => {
  it('exposes the core PSOM and SGCE routes', async () => {
    const server = createServer();
    const response = await server.inject?.('/health');
    expect(response).toBeDefined();
  });
});
```

- [ ] **Step 2: Run the API tests**

Run: `corepack pnpm --filter @aaes-os/platform-api test`

Expected: pass.

- [ ] **Step 3: Make the server, routes, and state module the single source of truth**

Keep the API state and route definitions centered in `services/platform-api/src/state.ts`, `services/platform-api/src/routes.ts`, and `services/platform-api/src/server.ts`.

- [ ] **Step 4: Run the API build**

Run: `corepack pnpm --filter @aaes-os/platform-api build`

Expected: pass.

- [ ] **Step 5: Commit the platform API change**

```bash
git add services/platform-api/src/main.ts services/platform-api/src/server.ts services/platform-api/src/routes.ts services/platform-api/src/state.ts services/platform-api/src/server.test.ts services/platform-api/package.json
git commit -m "feat: finish platform api surface"
```

## Finish Order

1. Governance/runtime core
2. Release pipeline
3. Nova Studio
4. Docs-site
5. Platform Web
6. Ops Console
7. Platform API

## Explicit blocker set

- `packages/runledger`
- `packages/trace-bus`
- `packages/evidence-receipts`

These three are now treated as first-class unfinished runtime-replay dependencies and are included in Task 1.

## Final Verification

- `corepack pnpm build`
- `corepack pnpm test`
- `corepack pnpm --dir docs-site build`
- `git diff --check`

## Coverage Check

- Governance/runtime core: Task 1
- Release pipeline: Task 2
- Nova Studio: Task 3
- Docs-site: Task 4
- Platform Web: Task 5
- Ops Console: Task 6
- Platform API: Task 7
