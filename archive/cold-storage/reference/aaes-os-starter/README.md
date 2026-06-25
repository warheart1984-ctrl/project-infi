# AAES-OS Starter — coding agent start here

Governed cognitive runtime scaffold enforcing invariants, traceability, and modular execution (e.g., Daniel).

This package is the **canonical TypeScript implementation** of [docs/contracts/AAES_OS_INTERFACE_V1.md](../../docs/contracts/AAES_OS_INTERFACE_V1.md) §1–4.

## Quick start

```bash
cd reference/aaes-os-starter
npm install
npm run build
npm test
```

## Layout

| Path | Role |
|------|------|
| `src/core/` | `AAESRequest`, `AAESContext`, pipeline records |
| `src/pipeline/` | Perception → deliberation → planning → action engines |
| `src/governance/` | Invariant and policy engines, audit logger |
| `src/modules/daniel/` | Example `ExecutionModule` |
| `src/uls/` | Universal Language Substrate stubs |
| `src/orchestrator.ts` | `AAESOrchestrator` — full step-traced pipeline |
| `manifests/modules.toml` | Module registry manifest |

## Related repo paths

- **Python reference (RFC trace bus):** `src/aaes_os/`
- **Trace-layer TS/Rust stubs:** `reference/aaes_os_v1/`
- **Extended monorepo copy (HTTP server, trace store):** `aaes-os/` at repo root
- **Formal spec:** `docs/contracts/AAES_OS_V1_FORMAL_SPEC.md`
- **Architecture:** `docs/contracts/AAES_OS_ARCHITECTURE_V1.md`

## Notes

- `DefaultActionEngine` returns an empty action list until plan→action derivation is implemented.
- JSON/API fields use `camelCase`; Rust and Python use `snake_case` (see interface contract §7.2).
