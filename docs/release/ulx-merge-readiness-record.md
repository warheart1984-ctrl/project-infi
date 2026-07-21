# ULX Merge Readiness Record

This record is an instantiated example of the reusable
[Constitutional Release Record Template](./constitutional-release-record-template.md).

## Constitutional Decision

- Decision ID: `ulx-merge-2026-07-12`
- Promotion: `Merge Candidate` -> `Approved Constitutional Merge`
- Release candidate version: `v0.1.0-rc.1`
- Candidate commit: `3ec9cab05666d04d74c75ce4b78a43b4560d6e1f`
- ULX follow-up commit: `56574617`
- Steward: `Jon Halstead`
- Assessment date: `2026-07-12`

## Packages Included

- `packages/ulx-governance`
- `packages/ulx-vm`
- `lawful-nova-shell/desktop`
- `docs/ulx/ulx-ide-integration.md`

## Build Verification

| Surface | Command | Result |
| --- | --- | --- |
| ULX governance | `pnpm --filter @aaes-os/ulx-governance build` | Pass |
| ULX VM | `pnpm --filter @aaes-os/ulx-vm build` | Pass |
| Nova Desktop / ULX host | `npm test` in `lawful-nova-shell/desktop` | Pass |

## Test Verification

| Surface | Command | Result |
| --- | --- | --- |
| ULX governance | `pnpm --filter @aaes-os/ulx-governance test` | Pass |
| Nova Desktop / ULX host | `npm test` in `lawful-nova-shell/desktop` | Pass |

## Smoke Verification

| Surface | Command | Result |
| --- | --- | --- |
| Lawful Nova verification | `powershell -NoProfile -ExecutionPolicy Bypass -File .\setup\verify.ps1` in `lawful-nova-shell` | Pass with 1 warning |
| Repo release verification | `pnpm run release:verify` | Pass |

The only warning in the Lawful Nova verification pass was the Nova API health probe not being reachable at `http://localhost:8080` during the local check. The script still completed successfully.

## Governance Verification

- ULX compilation is constitutionalized through `ConstitutionalCompiler`
- ULX bytecode acceptance is gated by `ULXValidator`
- ULX execution emits a traceable record through `ULXGovernanceRuntime`
- ULX commit requires trace presence via `ULXTraceInvariant`
- Repository freeze integrity verified successfully with `constitutional_freeze.py verify`
- Release verification succeeded after refreshing the release bundle signature and checksums

## Conformance Results

| Requirement | Status | Evidence |
| --- | --- | --- |
| Build gate | Satisfied | ULX governance, ULX VM, and Nova Desktop builds passed |
| Test gate | Satisfied | ULX governance tests and Nova Desktop tests passed |
| Smoke gate | Satisfied | Lawful Nova verify passed with non-blocking API warning |
| Governance gate | Satisfied | ULX runtime validation and trace invariant tests passed |
| Release gate | Satisfied | `pnpm run release:verify` passed |
| Freeze gate | Satisfied | `python constitutional_freeze.py verify` passed |

## Constitutional Requirements Satisfied

- Evidence before assertion
- Traceability from source to bytecode to trace
- Replayable ULX execution path
- Governance-gated validation before runtime commit
- Constitutional freeze integrity for the RC boundary
- Release bundle signature and checksum verification
- Clear truth boundary for the release receipt and docs

## Companion Specifications Referenced

- [Constitutional Release Record Template](./constitutional-release-record-template.md)
- [Launch Readiness Specification](./launch-readiness-specification.md)
- [ULX IDE Integration Map](../ulx/ulx-ide-integration.md)
- [Constitutional Release Receipt](./constitutional-release-receipt.md)
- [Docs Hub](../README.md)
- [Lawful Nova Shell README](../../lawful-nova-shell/README.md)

## Evidence Artifacts Produced

- [packages/ulx-governance/src/ulxGovernance.test.ts](/E:/project-infi/packages/ulx-governance/src/ulxGovernance.test.ts)
- [release/release-manifest.json](/E:/project-infi/release/release-manifest.json)
- [release/checksums.json](/E:/project-infi/release/checksums.json)
- [release/signature.json](/E:/project-infi/release/signature.json)
- [release/constitutional-release-receipt.json](/E:/project-infi/release/constitutional-release-receipt.json)
- [release/bundle/release-package.json](/E:/project-infi/release/bundle/release-package.json)
- [release/bundle/checksums.json](/E:/project-infi/release/bundle/checksums.json)
- [release/bundle/signature.json](/E:/project-infi/release/bundle/signature.json)
- [release/bundle/constitutional-release-receipt.json](/E:/project-infi/release/bundle/constitutional-release-receipt.json)
- [.runtime/cori-alpha/ledger/ledger-3ec9cab05666d04d74c75ce4b78a43b4560d6e1f.json](/E:/project-infi/.runtime/cori-alpha/ledger/ledger-3ec9cab05666d04d74c75ce4b78a43b4560d6e1f.json)
- [.runtime/cori-alpha/receipts/receipt-3ec9cab05666d04d74c75ce4b78a43b4560d6e1f.json](/E:/project-infi/.runtime/cori-alpha/receipts/receipt-3ec9cab05666d04d74c75ce4b78a43b4560d6e1f.json)
- [.runtime/cori-alpha/evidence/evidence-3ec9cab05666d04d74c75ce4b78a43b4560d6e1f.json](/E:/project-infi/.runtime/cori-alpha/evidence/evidence-3ec9cab05666d04d74c75ce4b78a43b4560d6e1f.json)

## Replay Reference

- `release/signature.json`
- `release/constitutional-release-receipt.json`
- `.runtime/cori-alpha/ledger/ledger-3ec9cab05666d04d74c75ce4b78a43b4560d6e1f.json`
- `lawful-nova-shell/desktop/tests/core.test.cjs`

## Known Limitations

- The Lawful Nova verify script reported a non-blocking Nova API health warning when the API was not running locally.
- The broader repository still contains unrelated noisy work outside the ULX merge slice.

## Remaining Follow-Up Items

- None blocking the ULX merge.
- Optional: run the Lawful Nova API locally before `setup/verify.ps1` if you want the warning to disappear.

## Stewardship Approval

Approved by Jon Halstead, Constitutional Steward-Architect.

This is the first documented constitutional release decision example for the ULX integration path.
