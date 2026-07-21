# Civilization OS — Organ Ledger

**Status:** Evidence map (v0.1)  
**Source of truth:** `G:\project-infi`  
**Method:** Top-level directory presence + Spec/Code/Tests probes + scorecard cross-check  
**Law:** Drive-G-1 — Status is the weakest verb justified by evidence  
**Date:** 2026-07-20

**Status vocabulary**

| Status | Meaning |
|--------|---------|
| `spec-only` | Docs/fixtures present; little or no executable surface found in-folder |
| `stub` | Code present; tests thin/absent |
| `partial` | Code + some tests or docs; not claimed production-complete |
| `verified-prototype` | Named as such in `docs/scorecards/project-infi.md` for this workspace pass |
| `empty-shell` | Directory exists but appears nearly empty (placeholder) |
| `unknown` | Exists; probe inconclusive — needs human classification |

---

## Core civilization organs

| Organ | Path | Spec | Code | Tests | Status | Notes |
|-------|------|------|------|-------|--------|-------|
| Identity freeze | `docs/civilization-os/IDENTITY.md` | Y | — | — | charter | This freeze |
| Constitutional (root tree) | `constitutional/` | ? | Y | Y | partial | Multiple entries; classify internals next pass |
| Constitutional substrate | `constitutional_substrate/` | N | N | Y | empty-shell / unknown | Sparse dir |
| Constitutional state | `constitutional_state/` | N | N | Y | empty-shell / unknown | Sparse dir |
| Governance artifacts | `governance/` | Y | N | Y | empty-shell / spec-only | Sparse; rich governance also under `docs-site/docs/governance/` |
| Governed memory | `governed_memory/` | Y | Y | Y | **partial (LIRL)** | Implemented via `packages/lirl/src/memory.ts`; top-level dir is placeholder — see `governed_memory/README.md` |
| Runtime law spine | `runtime_law_spine/` | N | N | N | empty-shell | Priority organ for vertical slice |
| Runtime | `runtime/` | N | Y | Y | partial | |
| Emergent substrate | `emergent-substrate/` | Y | Y | Y | partial | Has README |
| Receipts | `receipts/` | N | N | Y | empty-shell | Receipt packages also live under `packages/evidence-*` |
| Conformance | `conformance/` | Y | N | Y | partial | Fixtures present |
| Continuity engine | `continuity-engine/` | N | N | Y | unknown | |
| Evolve engine | `evolve_engine/` | N | N | Y | unknown | |
| AI organism entry | `ai_organism.py` + `docs/runtime/legacy/ai-organism.md` | Y | Y | partial | partial | Docstring claims “complete” — **parked**; treat as entry/integration scaffold |
| **LIRL vertical slice** | `packages/lirl/` + `services/platform-api/src/lirlRoutes.ts` | Y | Y | Y | **partial (tested)** | Lawful Intent Receipt Loop — package + HTTP; 5 vitest cases green |
| Symbolic organism tests | `tests/test_symbolic_organism_vm*` | — | — | Y | partial | Test artifacts exist |

---

## AAES / Nova / operator surfaces

| Organ | Path | Spec | Code | Tests | Status | Notes |
|-------|------|------|------|-------|--------|-------|
| Packages (governance spine) | `packages/` (e.g. `aaes-governance`, runtimes, ledgers) | Y | Y | Y | verified-prototype (subset) | Scorecard: governance/runtime spine |
| Services | `services/` (ops-console, platform-api, …) | Y | Y | Y | verified-prototype (subset) | Scorecard: ops-console |
| Lawful Nova shell | `lawful-nova-shell/` | Y | Y | Y | partial | |
| Nova studio | `nova-studio/` | Y | Y | N | partial | Scorecard mentions Nova Studio smoke |
| Nova mission 002 | `nova-mission-002/` | N | Y | N | stub | `.bak` sibling is noise — see SOURCE_OF_TRUTH |
| Nova (top) | `nova/` | N | N | Y | unknown | |
| Operator | `operator/` | N | Y | Y | partial | |
| Operator kernel | `operator_kernel/` | N | N | Y | unknown | |
| Operator surface | `operator-surface/` | N | Y | N | stub | |
| Observer | `observer/` | N | N | Y | empty-shell / unknown | |
| Sovereign IDE | `sovereign-ide/` | Y | Y | Y | partial | Serves `/api/organism/state` (UI/runtime hook) |
| Simulation / mesh | `simulation/` | Y | Y | Y | verified-prototype (mesh) | Scorecard: mesh-simulator tests |
| SDK | `sdk/` | Y | Y | Y | partial | |
| Core | `core/` | N | Y | Y | partial | |
| Frontend | `frontend/` | N | Y | Y | partial | |
| Standards | `standards/` | Y | Y | Y | partial | |
| Domain runtimes | `domain_runtimes/` | N | N | Y | unknown | Mythar/SRE bind here conceptually |
| Platform | `platform/` | N | N | Y | unknown | |
| CLI | `cli/` | N | N | Y | unknown | |
| App | `app/` | N | N | Y | unknown | |
| Docs hub | `docs/`, `docs-site/` | Y | — | — | verified-prototype (docs framing) | Scorecard |

---

## Secondary / lab / named engines

| Organ | Path | Spec | Code | Tests | Status |
|-------|------|------|------|-------|--------|
| AAES mirror dir | `aaes/`, `aaes-os/` | ? | ? | Y | unknown / sparse |
| AAIS | `aais/` | ? | ? | Y | unknown |
| Forge / forge_eval | `forge/`, `forge_eval/` | N | N | Y | unknown |
| Nexus | `nexus/` | Y | N | N | spec-only |
| IOGS | `iogs/` | N | N | N | unknown |
| Mechanic / Scorpion / Slingshot | `mechanic/`, `scorpion/`, `slingshot/` | N | N | Y | unknown |
| AI factory | `ai_factory/` | N | N | Y | unknown |
| Lab / training | `lab/`, `training/` | Y | N | Y | unknown / spec-only |
| Bindings | `bindings/` | N | N | N | unknown |
| External | `external/` | — | — | — | quarantine candidate |
| Archive (in-repo) | `archive/` | — | — | — | historical — not SoT for “current” |

---

## How to update this ledger

1. Change **Status** only when Spec/Code/Tests evidence changes.  
2. Promote to `verified-prototype` only with a fresh scorecard pass.  
3. Never promote to `live` / `complete` / `enforces` without runtime rejection proof + tests + receipt.

Next classification pass should expand `packages/*` into per-package rows (68 package dirs).

---

## Related

- Identity: `IDENTITY.md`  
- Vertical slice: `VERTICAL_SLICE.md`  
- Scorecard: `../scorecards/project-infi.md`
