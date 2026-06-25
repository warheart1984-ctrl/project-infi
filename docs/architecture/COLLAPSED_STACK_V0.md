# Collapsed stack v0.0 — constitutional substrate

**Status:** Move 1 + Move 2 implemented (substrate package + constitutional operator task slice)

This document merges the **collapse** strategy with what already exists in `E:\project-infi`. It is the north star for rebuild order; daily proof gates remain in [LAWFUL_NOVA_CODING_AGENT_PROOF.md](../operations/LAWFUL_NOVA_CODING_AGENT_PROOF.md).

---

## What “collapse” means (and does not)

| Collapse **is** | Collapse **is not** |
|-----------------|---------------------|
| One constitutional substrate instead of scattered runtimes | Deleting repos or inventing a new buzzword runtime |
| One law spine instead of half-wired RLS/UCR/AAIS governance | Flattening everything into one god-class |
| One state model instead of per-runtime ad-hoc status enums | Removing domain concepts |
| One receipt contract instead of bespoke JSON blobs | Breaking lawful Nova / operator proof paths |
| One observer story instead of “trust me, it works” | Skipping independent verification |

**Rebuild thesis:** collapse *conceptual layers* into a single governed substrate; keep domain runtimes as **views** on that substrate.

**Canonical home:** `E:\project-infi` (not `urg-wt` — worktree only; URG missions frozen by kill switch).

**Legacy clients (v0.0):** Nova API, Operator kernel, AAIS, URG — all become clients of the substrate, not separate state machines.

---

## Four strata (target v0.0)

```text
┌─────────────────────────────────────────────────────────────┐
│ 4. Observer Surface                                         │
│    Observer Verification Engine, Mission #001/#002 kits,      │
│    Operator / URG / AAIS consoles as views                  │
├─────────────────────────────────────────────────────────────┤
│ 3. Domain Runtime Facades                                   │
│    Truth, Sovereignty, Continuity, Reproduction, …          │
│    = spec + receipt types + events → CSR transitions        │
├─────────────────────────────────────────────────────────────┤
│ 2. Evidence & Receipt Layer                                 │
│    EvidenceBundle, Receipt v2 (six dimensions),             │
│    Constitutional Transition Ledger (receipt-keyed)         │
├─────────────────────────────────────────────────────────────┤
│ 1. Constitutional Substrate                                 │
│    Runtime Constitution, CSR, Runtime Law Spine             │
│    (measured boot, sealed trust root, fail-closed)          │
└─────────────────────────────────────────────────────────────┘
         ▲              ▲              ▲              ▲
         │              │              │              │
      Nova API    Operator kernel    AAIS spans    URG missions
      (8080)         (8790)           (8000)      (in-process)
```

Everything else is a **client** of strata 1–2.

---

## Repo inventory — what exists today

### Stratum 1 — Constitutional substrate (partial)

| Piece | Location | Wired to clients? |
|-------|----------|-------------------|
| Runtime Law Spine gate | `runtime_law_spine/` | **Yes** — `aais/launcher.py`, `operator_kernel/main.py` (`ensure_rls_sealed`) |
| UCR trust root | `src/ucr/trust_root.py` | Partial |
| Runtime constitution (articles) | `governance/`, `docs/contracts/` | Docs + genomes; not single runtime package |
| CSR spec | [CONSTITUTIONAL_STATE_RUNTIME.md](../contracts/CONSTITUTIONAL_STATE_RUNTIME.md) | Spec complete |

**Gap:** constitution + CSR unified in `constitutional_substrate/`; thin duplicates remain in `nova/constitutional_state.py`, `src/fos/constitutional_state.py` (consolidate later).

### Stratum 2 — Evidence & receipts (strongest in operator_kernel)

| Piece | Location | Notes |
|-------|----------|-------|
| Receipt v2 + six dimensions | `operator_kernel/receipts_v2.py` | `BaseReceiptV2`, domain receipts, `TransitionReceiptV2` |
| Evidence bundle | `receipts_v2.EvidenceBundleV2` | In same module |
| Transition ledger | `operator_kernel/transition_ledger.py` | `ConstitutionalTransitionLedger` — transitions keyed by `receipt_id` |
| CSR models | `operator_kernel/constitutional_state.py` | `StateObject`, `StateTransition`, `replay_state` |
| Amendment engine | `operator_kernel/amendments.py` | Article XIV lifecycle |
| Mission receipt v2 (URG) | `src/ugr/mission/mission_receipt.py` | Parallel path; not yet unified ledger |

**Gap:** AAIS span/plan receipts and operator task receipts do not all flow through one ledger file/API yet.

### Stratum 3 — Domain facades (scaffolded)

| Domain | Spec | Python scaffold | Wired to CSR? |
|--------|------|-----------------|---------------|
| Personal continuity | [01-personal-continuity.md](../contracts/domain-runtimes/01-personal-continuity.md) | `domain_runtimes/personal_continuity.py` | Register only (`csr_bridge`) |
| Relationship | [02-relationship.md](../contracts/domain-runtimes/02-relationship.md) | `domain_runtimes/relationship.py` | Register only |
| Cognitive | [03-cognitive.md](../contracts/domain-runtimes/03-cognitive.md) | `domain_runtimes/cognitive.py` | Register only |
| Founder | [04-founder.md](../contracts/domain-runtimes/04-founder.md) | `domain_runtimes/founder.py` | Register only |
| Opportunity | [05-opportunity.md](../contracts/domain-runtimes/05-opportunity.md) | `domain_runtimes/opportunity.py` | Register only |
| Reputation | [06-reputation.md](../contracts/domain-runtimes/06-reputation.md) | `domain_runtimes/reputation.py` | Register only |
| Burnout | [07-burnout.md](../contracts/domain-runtimes/07-burnout.md) | `domain_runtimes/burnout.py` | Register only |
| Operator tasks | `operator_kernel/agent_loop.py` | `constitutional_task.py` | **Yes** — full vertical slice |

Index: [domain-runtimes/INDEX.md](../contracts/domain-runtimes/INDEX.md).

**Gap:** Domain receipt emitters + remediation closures not wired; only `operator_task` has transitions, JSONL receipts store, and observer packets.

### Stratum 4 — Observer surface (started)

| Piece | Location | Mission |
|-------|----------|---------|
| Observer Verification Engine | `operator_kernel/observer_verification.py` | Replay + verify against ledger |
| Mission #002 kit | `nova-observer-bundle/`, [NOVA_CURSOR_MISSION_002.md](../proof/NOVA_CURSOR_MISSION_002.md) | Nova × Cursor × Nemotron |
| Mission #001 analogue | `observer-bundle/` | Continuity / Bone King |
| Operator proof script | `docs/operations/LAWFUL_NOVA_CODING_AGENT_PROOF.md` | Lawful LLM + coding agent |

**Gap:** Mission #002 Category B still open; operator tasks emit observer packets — Nova lawful turn path not yet unified.

### Legacy / parallel substrates (do not expand)

These are **organs** or **execution substrates**, not the constitutional center:

- `src/ul_substrate.py`, `src/aais_ul_substrate.py` — ForgeGate command substrate
- `src/continuity/substrate.py`, `nova/continuity/substrate.py` — continuity organ
- `src/otem_execution_substrate.py` — OTEM execution

Mark as **clients or adapters**, not second state machines.

---

## Rebuild order (no hand-waving)

### Step 1 — Freeze and mark ✅ (operator posture)

- [x] Stop adding new runtimes (team rule)
- [x] AAIS/URG/Operator/Nova marked legacy **clients** in [E_DRIVE_PRODUCTION_LAYOUT.md](../operations/E_DRIVE_PRODUCTION_LAYOUT.md)
- [x] Canonical repo: `project-infi`
- [x] URG kill switch + unlawful agent block for safety

### Step 2 — Build substrate cleanly (in progress)

| Deliverable | Action |
|-------------|--------|
| `constitutional_substrate/` package | Extract from `operator_kernel/{constitutional_state,transition_ledger,receipts_v2,amendments,observer_verification}.py`; operator imports from package |
| RLS gate | Already on AAIS + operator; add URG mission entry when kill switch lifted |
| Fail-closed pipelines | `src/cog_runtime/formal/spine_pipeline.py` — extend coverage |
| Receipt v2 TS mirror | Already in `aaes-os/packages/governed-memory/` — keep in sync |

**v0.0 done when:** substrate importable as one package; tests pass without `operator_kernel` owning the models.

### Step 3 — Collapse runtimes into views

For each runtime:

1. Fill [Unified Runtime Specification Template](../contracts/) (where started).
2. Remove runtime-local status enums where CSR `StateObject` applies.
3. Emit runtime-specific Receipt v2 → `ConstitutionalTransitionLedger.append(transition, receipt)`.

**First vertical slice:** operator `operator_task` only (smallest surface).

### Step 4 — Rewire clients

| Client | Pattern |
|--------|---------|
| Operator `:8790` | task create → register `StateObject`; status change → Receipt v2 → ledger |
| URG missions | `mission` state object; `build_mission_receipt_v2` → ledger |
| AAIS spans | span state → CSR; cognitive receipts drive transitions |

Do **not** rebuild AAIS as a new runtime — reframe as best substrate client.

### Step 5 — Observer Kit as proof harness

Build on CSR + ledger + Receipt v2:

- Mission #002: Nova × Cursor × Nemotron — emit full observer packet (state + receipts + replay)
- Mission #001: continuity bundle analogue
- Outsider runs kit commands only; pass/fail without founder narration

---

## Next three moves (concrete)

These are the only priorities until one vertical slice is fully governed end-to-end.

### Move 1 — `constitutional_substrate/` package ✅

```
constitutional_substrate/
  __init__.py
  constitutional_state.py
  transition_ledger.py
  receipts_v2.py
  amendments.py
  observer_verification.py
  runtime.py
```

- Operator kernel re-exports from substrate.
- Tests: `tests/constitutional_substrate/`, `tests/operator_kernel/`.

### Move 2 — One fully constitutional operator task ✅

Wired via `operator_kernel/csr.py`, `constitutional_task.py`, `status_mapping.py`, `receipts_store.py`, `observer_packet.py`, `agent_loop.py`.

**Pass criteria (met for operator slice):**

- Reconstruct task state from receipts (`CSR.replay`)
- Observer verification + packet under `.runtime/observer_packets/<task_id>/`
- Operator kernel tests green (74+)

### Move 3 — Mission #002 = Observer Kit v0.0

For the Nova × Cursor × Nemotron path you already proved locally:

1. After a lawful `/v1/chat` turn (or one operator task), emit:
   - canonical `StateObject` snapshot
   - receipt chain (Receipt v2)
   - replay result JSON
2. Package as `nova-observer-bundle/v0/` observer packet (extend existing bundle).
3. Document outsider commands in `nova-observer-bundle/verification/instructions.md`.
4. Close Mission #002 only on **Category B** independent reproduction ([dossier](../proof/NOVA_CURSOR_MISSION_002_DOSSIER.md)).

---

## Vertical slice definition (the pattern to replicate)

When **one** operator task satisfies all of:

| # | Check |
|---|--------|
| 1 | `StateObject` registered at create |
| 2 | Every status change has `TransitionReceiptV2` in ledger |
| 3 | `RuntimeLawSpineGate.require_sealed()` at kernel boot |
| 4 | `run_observer_verification()` passes |
| 5 | `replay_state(seed, ledger)` matches final `StateObject` |
| 6 | E2E + red team still pass |

…collapsing Truth, Sovereignty, Reproduction, AAIS spans becomes **pattern replication**, not a scary rewrite.

---

## What not to do during v0.0

- Do not delete `urg-wt` / worktrees until substrate slice is green (archive later).
- Do not merge AAIS mock and frontier into one process — keep ports; unify **state** not **binaries**.
- Do not add new per-runtime status enums — extend `StateObjectType` in one place.
- Do not claim GA / continuity-grade until Mission #002 Category B closes.

---

## Related docs

| Doc | Role |
|-----|------|
| [CONSTITUTIONAL_STATE_RUNTIME.md](../contracts/CONSTITUTIONAL_STATE_RUNTIME.md) | CSR contract (Article XV) |
| [CONSTITUTIONAL_RUNTIME_V0_1.md](../contracts/CONSTITUTIONAL_RUNTIME_V0_1.md) | Runtime versioning |
| [constitutional-runtime.md](../constitutional-runtime.md) | Nova v0.1 vs v0.2 (legacy bridge note) |
| [LAWFUL_NOVA_CODING_AGENT_PROOF.md](../operations/LAWFUL_NOVA_CODING_AGENT_PROOF.md) | Prove Lawful LLM + coding agent today |
| [NOVA_CURSOR_MISSION_002.md](../proof/NOVA_CURSOR_MISSION_002.md) | Observer / system proof |
| [AAES_GOVERNED_MEMORY_TRI_STRATA.md](../contracts/AAES_GOVERNED_MEMORY_TRI_STRATA.md) | Law spine entrypoints |

---

## Decision log

| Date | Decision |
|------|----------|
| 2026-06-23 | Substrate home = `project-infi`; collapse = views on CSR, not repo deletion |
| 2026-06-23 | First wired client = Operator kernel (8790); first proof = Mission #002 observer packet |
