# Architect Agent Published-Dist Smoke Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prove the packed `@aaes-os/architect-agent` ESM package executes a deterministic governed act through consumer `node_modules` resolution on Linux and Windows.

**Status:** Complete. Packed smoke, workspace tests, CTS, and scoped diff checks passed on 2026-06-30.

**Architecture:** A Node smoke runner discovers the full workspace runtime dependency closure rooted at architect-agent, builds it, stages publishable manifests with exact versions in place of `workspace:*`, packs every package, and installs all local tarballs into an isolated consumer. A separate Node process imports the public package name; package security documentation and a Node 20 Windows CI job cover the runtime boundary and Windows package layout.

**Tech Stack:** Node.js ESM, pnpm 10.15.0, TypeScript package builds, Node `assert`, GitHub Actions.

---

### Task 1: Establish The Red Published-Package Command

**Files:**
- Modify: `package.json`
- Modify: `packages/architect-agent/package.json`

- [ ] **Step 1: Add smoke commands that reference the not-yet-created runner**

Add this root script:

```json
"smoke:architect-agent": "corepack pnpm --filter @aaes-os/architect-agent run smoke:dist"
```

Add this package script:

```json
"smoke:dist": "node scripts/smoke-dist.mjs"
```

- [ ] **Step 2: Run the smoke command and verify the red state**

Run:

```powershell
corepack pnpm smoke:architect-agent
```

Expected: FAIL with `ERR_MODULE_NOT_FOUND` for
`packages/architect-agent/scripts/smoke-dist.mjs`.

### Task 2: Implement The Packed Consumer Smoke

**Files:**
- Create: `packages/architect-agent/scripts/smoke-dist.mjs`
- Create: `packages/architect-agent/test/smoke-dist-consumer.mjs`

- [ ] **Step 1: Create the consumer harness**

The harness must import only from `@aaes-os/architect-agent`, execute the same
two-target input twice, and assert:

```js
assert.equal(act.integration.envelopes.length, 1);
assert.deepEqual(
  act.integration.envelopes[0].patches.map((patch) => patch.path),
  ['src/existing.ts', 'src/new.ts'],
);
assert.equal(act.integration.envelopes[0].patches[0].reverse_patch.operation, 'restore');
assert.equal(act.integration.envelopes[0].patches[1].reverse_patch.operation, 'delete');
assert.equal(act.egl.equivalent, true);
assert.equal(act.safety.verdict, 'ALLOW');
assert.equal(act.receipt.kind, 'runtime');
assert.equal(Object.isFrozen(act), true);
assert.equal(Object.isFrozen(act.integration.envelopes[0]), true);
assert.equal(repeated.act_id, act.act_id);
assert.equal(repeated.integration.envelopes[0].envelope_id, act.integration.envelopes[0].envelope_id);
assert.equal(repeated.receipt.receiptId, act.receipt.receiptId);
```

Print one JSON line:

```js
process.stdout.write(`${JSON.stringify({
  status: 'ok',
  act_id: act.act_id,
  envelope_id: act.integration.envelopes[0].envelope_id,
  receipt_id: act.receipt.receiptId,
  egl: act.egl.criterion_id,
})}\n`);
```

- [ ] **Step 2: Create the smoke runner**

Implement `packages/architect-agent/scripts/smoke-dist.mjs` with:

- `mkdtemp`, `mkdir`, `writeFile`, `copyFile`, and `rm` from
  `node:fs/promises`;
- `spawnSync` with argument arrays and captured output;
- workspace package discovery from `packages/*/package.json`;
- recursive traversal of `workspace:*` runtime dependencies starting at
  `@aaes-os/architect-agent`;
- package builds using `corepack pnpm --filter <package> run build`;
- staged package directories containing `package.json`, `dist`, and available
  README/SECURITY files;
- staged manifests with every closure `workspace:*` dependency replaced by the
  target package's exact version;
- local tarballs created from each staged package;
- a consumer manifest whose dependencies bind every closure package to its
  `file:` tarball;
- `corepack pnpm install --lockfile-only --offline --ignore-scripts`;
- `corepack pnpm install --offline --frozen-lockfile --ignore-scripts`;
- a child `node smoke-dist-consumer.mjs` launched with `cwd` set to the
  consumer;
- JSON parsing that requires `status === 'ok'`;
- cleanup in `finally` limited to the exact directory returned by `mkdtemp`.

Command failures must include the phase, exit status, stdout, and stderr.

- [ ] **Step 3: Run the packed consumer smoke**

Run:

```powershell
corepack pnpm smoke:architect-agent
```

Expected: exit 0 and one JSON line with `status: "ok"`, `act_id`,
`envelope_id`, `receipt_id`, and `egl: "EGL-1"`.

- [ ] **Step 4: Run the package build and focused unit tests**

Run:

```powershell
corepack pnpm --filter @aaes-os/architect-agent run build
corepack pnpm --filter @aaes-os/architect-agent run test
```

Expected: both commands exit 0; eight architect-agent tests pass.

### Task 3: Document The Runtime Security Boundary

**Files:**
- Create: `packages/architect-agent/SECURITY.md`
- Modify: `packages/architect-agent/README.md`

- [ ] **Step 1: Add the package security document**

Document these concrete properties:

- Runtime inputs are structured objects supplied by the caller.
- UGR/CMC derivation, planning, hashing, envelope construction, replay,
  safety, and evidence receipt construction happen in memory.
- Runtime code performs no filesystem reads/writes, network access, process
  spawning, environment reads, dynamic code loading, or patch application.
- Raw previous file content is embedded in reverse patches and is sensitive.
- Deterministic SHA-256/SHA3-256 identifiers are integrity evidence, not
  signatures, authentication, authorization, identity, or non-repudiation.
- The caller owns input authorization, snapshot honesty, receipt persistence,
  mutation execution, sandboxing, durable ledgers, and key-backed signing.
- The smoke runner is development/CI tooling outside the runtime boundary and
  writes only to its unique OS temporary directory.

Include a concise STRIDE table covering forged replay, envelope tampering,
repudiation limits, reverse-content disclosure, file-cap denial of service,
and incomplete-target elevation attempts.

- [ ] **Step 2: Link the security document and smoke command**

Add to `packages/architect-agent/README.md`:

```markdown
See [SECURITY.md](SECURITY.md) for the package threat model, trust assumptions,
side-effect inventory, and non-goals.
```

Add to Verification:

```bash
pnpm smoke:architect-agent
```

### Task 4: Add Windows Published-Package CI

**Files:**
- Modify: `.github/workflows/ci.yml`

- [ ] **Step 1: Add a Node 20 Windows job**

Add a `smoke-dist-windows` job using:

```yaml
smoke-dist-windows:
  runs-on: windows-latest
  steps:
    - name: Checkout
      uses: actions/checkout@v4
    - name: Setup Node
      uses: actions/setup-node@v4
      with:
        node-version: 20
    - name: Enable Corepack
      run: corepack enable
    - name: Install dependencies
      run: pnpm install --frozen-lockfile
    - name: Smoke packed architect-agent package
      run: pnpm smoke:architect-agent
```

- [ ] **Step 2: Validate workflow syntax structurally**

Run:

```powershell
Get-Content -Raw .github\workflows\ci.yml
```

Expected: `build-test` remains unchanged and `smoke-dist-windows` is a sibling
job with correctly indented steps.

### Task 5: Final Verification

**Files:**
- Verify all scoped implementation files.

- [ ] **Step 1: Run the published-dist smoke again**

Run:

```powershell
corepack pnpm smoke:architect-agent
```

Expected: exit 0 with deterministic IDs and `egl: "EGL-1"`.

- [ ] **Step 2: Run the full workspace build and test suite**

Run:

```powershell
corepack pnpm test
```

Expected: all workspace package builds and all Vitest tests pass.

- [ ] **Step 3: Run CTS**

Run:

```powershell
corepack pnpm test:cts
```

Expected: 23 CTS files and 36 tests pass.

- [ ] **Step 4: Check the scoped diff**

Run:

```powershell
git diff --check -- aaes-os/package.json aaes-os/packages/architect-agent aaes-os/.github/workflows/ci.yml aaes-os/docs/superpowers
```

Expected: exit 0 with no whitespace errors.
