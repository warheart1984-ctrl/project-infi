# AAES-OS v1.0 — CHANGELOG

All changes tracked with governance awareness: no architectural drift, no silent invariant changes, no ungoverned runtime behavior.

---

## [Unreleased]

### Added

- Minimal CRK-1 deterministic run loop (init → execute → finalize) via UCRRuntime.
- Governance Engine with invariant enforcement (`packages/aaes-governance`).
- CTS tests for invariants and determinism (vitest + pytest).
- Minimal CDP-1 runner (`benchmarks/cdp1/runMinimalCDP1.ts`) and CEP orchestrator.
- Deterministic replay validator (`tools/validateDeterministicReplay.ts`).
- Release dashboard, evidence ledger, Version 2.0 backlog, release manager checklist.
- Governance Council review packet and replication package README.
- Release gatekeeper and release notes generator scripts.

### Changed

- Runtime wiring routes runs through Governance Engine when configured.
- Ledger integration via RunStore for span and run records.

### Governance Notes

- No new constitutional objects added.
- No new invariants beyond the initial core set without Council approval.
- All new behavior produces ledger records and passes through governance when enabled.
- Version 2.0 ideas captured in `VERSION_2_BACKLOG.md` instead of expanding v1.0.

---

## [v1.0.0] — (target)

To be populated once all release gates are satisfied and replication is complete.
