# Architect Agent Published-Dist Smoke Design

**Status:** Approved for implementation on 2026-06-30.

## Goal

Prove that the publishable `@aaes-os/architect-agent` package executes one
governed act through its built ESM entrypoint and normal `node_modules`
resolution. The proof must not depend on TypeScript execution, Vitest aliases,
or direct source imports.

## Selected Approach

Use a temporary consumer project populated from package tarballs. The smoke
runner discovers the complete `workspace:*` runtime dependency closure rooted
at `@aaes-os/architect-agent`, stages publishable copies with workspace
protocols converted to exact package versions, packs every package in the
closure, installs those tarballs into the temporary project with pnpm, then
launches a separate Node process from that project.

This approach exercises:

- package manifests and `exports`;
- generated `dist` JavaScript;
- transformed workspace dependency versions in packed manifests;
- pnpm's consumer-facing `node_modules` layout on Windows and Linux;
- package-name imports from outside the monorepo.

The temporary consumer is preferable to a direct `node dist/index.js` call
because the latter does not prove dependency or package export resolution.

## Components

### Smoke Runner

`packages/architect-agent/scripts/smoke-dist.mjs` owns orchestration:

1. Locate the workspace and package directories.
2. Create a unique temporary directory under the operating-system temp root.
3. Discover the complete workspace runtime dependency closure.
4. Build every package in that closure.
5. Stage and pack each package into a local tarball.
6. Create a minimal consumer `package.json` that binds every closure package
   to its local tarball.
7. Install all tarballs with pnpm using a frozen, network-independent local
   dependency set.
8. Launch the consumer harness with `process.execPath`.
9. Forward useful child output and fail on any nonzero status.
10. Remove only the temporary directory created by this run.

The runner uses argument arrays rather than shell-built command strings.

### Consumer Harness

`packages/architect-agent/test/smoke-dist-consumer.mjs` is copied into the
temporary consumer and imports:

```js
import {
  ArchitectAgentLoop,
  createDefaultUnifiedGovernanceContract,
} from '@aaes-os/architect-agent';
```

It executes one deterministic two-target act and asserts:

- the public package resolves from `node_modules`;
- one immutable envelope contains both ordered targets;
- exact restore and delete reverse operations are present;
- `pre_state_hash` is populated;
- EGL-1 reports equivalence;
- safety returns `ALLOW`;
- the runtime evidence receipt binds the allowed act;
- repeating the same input yields identical act, envelope, and receipt IDs.

Successful execution prints one compact JSON record containing `status`,
`act_id`, `envelope_id`, `receipt_id`, and `egl`.

### Package Scripts

The architect-agent package exposes:

- `smoke:dist`: runs the smoke runner;

The workspace exposes the same command through a root `smoke:architect-agent`
script for local and CI use.

## Windows CI

Add a dedicated `windows-latest` job using Node 20 and pnpm 10.15.0. It performs
a frozen workspace install and invokes the root smoke script. Node 20 matches
the repository's existing CI baseline and avoids treating the current local
Node 24 workspace-link failure as package behavior.

The smoke runner never deletes or repairs workspace `node_modules` entries.
Staged manifests reproduce pnpm's publish-time `workspace:*` conversion without
requiring workspace links. All install activity occurs in its own temporary
consumer directory, so stale workspace links cannot be mistaken for
publishable-package failures.

## Error Handling

Every child command is checked for:

- spawn errors;
- nonzero exit status;
- missing expected output.

Failure messages identify the command phase and include captured standard
output and standard error. Cleanup executes in `finally`, and it verifies that
the removal target is the exact temporary directory created by the runner.

## Security Boundary Documentation

Add `packages/architect-agent/SECURITY.md` and link it from the package README.
The document records the actual implementation:

- all contract, planning, hashing, replay, safety, and receipt construction is
  in memory;
- the package reads no files, applies no patches, writes no receipt files,
  accesses no network, reads no environment variables, and spawns no child
  processes;
- the caller supplies pre-state content and an issuance timestamp;
- reverse patches contain raw prior file content and may therefore be
  sensitive;
- SHA-256 and SHA3-256 values provide deterministic integrity, not identity,
  authentication, authorization, signatures, or non-repudiation;
- durable ledgers, mutation executors, key-backed signing, sandboxing, and
  trust anchors remain outside this package.

The smoke runner itself is development and CI tooling, not part of the runtime
security boundary. It spawns pnpm and Node and writes only to its temporary
consumer directory.

## Test Strategy

Implementation follows a red-green sequence:

1. Add the package/root smoke scripts before the runner exists and confirm the
   command fails because the runner is missing.
2. Add the runner and consumer harness.
3. Run `smoke:architect-agent` and require successful packed-package execution.
4. Run the architect-agent unit tests and package build.
5. Run the full workspace test suite and CTS.
6. Run `git diff --check` on the scoped files.

## Non-Goals

- Applying patches to the real filesystem.
- Persisting evidence receipts.
- Repairing arbitrary workspace `node_modules` directories.
- Supporting CommonJS; the published package is ESM.
- Adding key-backed signing or remote trust services.
