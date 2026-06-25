# Architecture

Canonical architecture contract: [docs/contracts/AAES_OS_ARCHITECTURE_V1.md](../../../docs/contracts/AAES_OS_ARCHITECTURE_V1.md)

## Four layers

1. **Interface** — HTTP `/aaes/execute`, request admission
2. **Cognitive Runtime** — perception → deliberation → planning → action
3. **Governance & Invariants** — `InvariantEngine`, `PolicyEngine`, audit trace
4. **Persistence & Integration** — trace store, ledger bridges

This starter implements layer 2–3 stubs. Wire persistence and HTTP in product code or `aaes-os/` at repo root.
