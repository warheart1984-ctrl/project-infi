# AAES-OS Roadmap

Sequential phases, dependencies, and Definition-of-Done criteria.

## Phase 1 — Foundation & Workspace

**Status:** Done · **Priority:** —

- pnpm monorepo, TypeScript workspace, branded types, base configs

**Definition of Done:** Project compiles; shared types available; workspace stable.

---

## Phase 2 — Core Data & Eventing

**Status:** Done · **Priority:** —

- In-memory RunLedgerStore, TraceBusClient, spans, invariant links, integration tests

**Definition of Done:** Spans emit correctly; ledger records runs; invariant links resolvable.

---

## Phase 3 — UCR Runtime Core

**Status:** Stubs only · **Priority:** High

- UCRRuntime shell, execution loop, run lifecycle, basic span emission

**Definition of Done:** Deterministic execution loop; lifecycle init → execute → finalize; minimal run completes end-to-end.

---

## Phase 4 — Governance Engine

**Status:** Stubs only · **Priority:** High

- InvariantEngine, FaultJournalStore, basic enforcement

**Definition of Done:** Invariants validated; faults journaled; enforcement blocks invalid transitions; CTS passes.

---

## Phase 5 — Tri-Core Protocol

**Status:** Types only · **Priority:** Medium

- Triad governance model and protocol logic

**Definition of Done:** Governance cycles execute; protocol messages validated; deterministic transitions enforced.

---

## Phase 6 — Persistence Layer

**Status:** Not started · **Priority:** High

- Durable RunLedger (SQLite or file-based), migration, deterministic replay

**Definition of Done:** Runs persist across restarts; replay produces identical results; crash-safe writes.

---

## Phase 7 — Ops Console v2

**Status:** Basic version done · **Priority:** Medium

- Real runtime integration, pause/resume, invariant views, fault journal viewer

**Definition of Done:** Console reflects real runtime state; operator controls functional.

---

## Phase 8 — Infra & Observability Polish

**Status:** Snippets only · **Priority:** Low

- Prometheus/Grafana, alerting, deployment story

**Definition of Done:** Metrics exposed; dashboards available; example deployment provided.

---

## Phase 9 — Integration & Examples

**Status:** Not started · **Priority:** Medium

- Sample agents, Python interop, end-to-end demos

**Definition of Done:** Real-world usage examples; cross-language interop validated.

---

## Phase 10 — Advanced Governance

**Status:** Future · **Priority:** Future

- Sigils, provenance ledger, self-patching, policy-as-code

**Definition of Done:** Higher-order governance features validated; deterministic enforcement.

---

Full launch docs: [docs/aaes-os/](../../docs/aaes-os/)
