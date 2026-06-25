# CAS 1.0 — Constitutional Architecture Specification

## 1. Purpose

CAS 1.0 defines the **object model** for governed cognition in AAES-OS. It is the contract between:

- Agents / models
- The CRK-1 runtime
- The governance layer
- The ledger and replication machinery

CAS 1.0 must be **independently implementable** and **conformance-testable** via CTS.

Reference implementation: `aaes-os/runtime/crk1/`

---

## 2. Core Objects

### 2.1 Identity

**Role:** Represents a principal (agent, model, operator).

**Fields (canonical):**

- `id: string`
- `type: "agent" | "model" | "operator"`
- `metadata: Record<string, unknown>`

**Invariants:**

- `id` is globally unique
- `type` is from the allowed set

---

### 2.2 Run

**Role:** A single governed execution.

**Fields:**

- `runId: string`
- `identity: Identity`
- `payload: Record<string, unknown>`
- `createdAt: ISO8601 string`

**Invariants:**

- `runId` unique
- `payload` non-empty (`INV.NO_EMPTY_PAYLOAD`)

---

### 2.3 Span

**Role:** A typed event within a run.

**Fields:**

- `spanId: string`
- `runId: string`
- `type: "init" | "execute" | "finalize" | ...`
- `timestamp: number` (monotonic within run)
- `data?: Record<string, unknown>`

**Invariants:**

- At least one `execute` span per successful run (`INV.MUST_EMIT_EXECUTE_SPAN`)

---

### 2.4 Receipt

**Role:** Immutable record of a completed run.

**Fields:**

- `runId: string`
- `hash: string` (content-addressed)
- `spans: Span[]`
- `result: unknown`
- `createdAt: ISO8601 string`

**Properties:**

- Deterministic: same input → same receipt → same hash

---

### 2.5 Fault

**Role:** Record of an invariant violation.

**Fields:**

- `runId: string`
- `invariantId: string`
- `message: string`
- `timestamp: ISO8601 string`

---

## 3. Allowed Transitions

### 3.1 Run Lifecycle

- `NewRun` → `Init` → `Execute` → `Finalize` → `Receipt`
- Any invariant failure → `Fault` (no receipt)

No other transitions are allowed in CAS 1.0.

---

## 4. Conformance (CTS)

A CAS 1.0 implementation is conformant if:

- It implements all core objects with required fields
- It enforces all CAS-level invariants
- It passes the CTS suite under `aaes-os/tests/cts/`:

  - Identity tests
  - Run lifecycle tests
  - Span emission tests
  - Receipt determinism tests
  - Fault emission tests

Run: `cd aaes-os && pnpm test:cts`

---

## 5. Release Gate

> **CAS 1.0 is considered stable when an independent implementation passes CTS with zero modifications.**

---

## 6. Versioning

- CAS 1.0 is **frozen** for AAES-OS v1.0
- Any new objects or invariants → CAS 1.1+ → [Version 2.0 backlog](../../aaes-os/VERSION_2_BACKLOG.md)
