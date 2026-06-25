# AAES-OS v1 Reference Stubs

Language-agnostic contract: [docs/contracts/AAES_OS_INTERFACE_V1.md](../../docs/contracts/AAES_OS_INTERFACE_V1.md)

Formal trace spec: [docs/contracts/AAES_OS_V1_FORMAL_SPEC.md](../../docs/contracts/AAES_OS_V1_FORMAL_SPEC.md)

Python reference implementation: `src/aaes_os/` (normative for trace bus behavior).

These folders are **starter stubs** for coding agents. Fill in orchestration, policy, persistence, and HTTP handlers; keep field names aligned with the interface contract.

## Starter layout

```
reference/aaes_os_v1/
  README.md                 ← this file
  typescript/
    package.json
    tsconfig.json
    src/
      index.ts              re-exports
      types.ts              enums + records
      error.ts              Result / AaesError helpers
      trace_bus.ts          TraceBus stub
      governed_span.ts      GovernedSpan stub
      orchestrator.ts       CognitiveOrchestrator stub
      invariant_engine.ts   span InvariantEngine stub
      policy_engine.ts      PolicyEngine stub
      uls.ts                  ULS stub
      modules/daniel.ts       DanielModule stub
      api.ts                  HTTP route types / handler stubs
  rust/
    Cargo.toml
    src/
      lib.rs
      types.rs
      error.rs
      trace_bus.rs
      governed_span.rs
      orchestrator.rs
      invariant_engine.rs
      policy_engine.rs
      uls.rs
      modules/daniel.rs
```

## Validation commands

```bash
# Python (from repo root)
python -m pytest tests/test_aaes_os_v1.py -q

# TypeScript
cd reference/aaes_os_v1/typescript && npm install && npx tsc --noEmit

# Rust
cd reference/aaes_os_v1/rust && cargo check
```

## Agent fill order

1. `types.ts` / `types.rs` — already mirror the contract; extend only with backward-compatible fields.
2. `trace_bus` + `governed_span` — port logic from `src/aaes_os/trace_bus.py` and `governed_span.py`.
3. `invariant_engine` — wire `InvariantId` checks before append.
4. `policy_engine` + `uls` — admission normalization and governor decisions.
5. `modules/daniel` — pluggable module example.
6. `orchestrator` — compose steps; call `governedAction` sequence.
7. `api` — expose HTTP shapes from interface §10.
