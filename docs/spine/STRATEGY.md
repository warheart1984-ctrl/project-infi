# Project Infinity — Strategy

**Status:** asserted (2026-06-08)  
**Owner:** operator + platform  
**Canonical repo root:** `e:\project-infi` (treat `Project-Infinity1/` nested tree as mirror only — edit the repo root)

This document connects product vision, operational doctrine, blueprint scope, and phased execution. It does not override runtime code or active contracts.

---

## Vision (product north star)

Source: [`The Vision.txt`](../_archive/workspace_pull/external-archives/workspace-root-notes/The%20Vision.txt)

- The product is the selling point. The user is not the commodity.
- Sell the intelligence. Never sell the person.
- The value lives in the product, not in ownership of the user.
- Monetize the work. Never monetize the human.

**Monetization boundary:** Revenue comes from governed intelligence (runtime seats, workflow packs, federation tiers). No operator data resale, no commoditization of people.

---

## Doctrine

Operational translation: [Stabilize and Free](./STABILIZE_AND_FREE.md)

- **Stabilize first** — law, verification, bounded behavior before expansion.
- **Free the operator** — system carries correctness, flow, and reference (CLR), not hidden shortcuts.
- **Decision rule** — if stability is unclear: slow, reject, wait, degrade, or require review.

Founding narrative (non-operational): [ANAMNESIS.md](../foundation/ANAMNESIS.md)

---

## System stack (blueprint)

Authority: [`document/blueprints/PROJECT_BLUEPRINTS_MASTER.md`](../../document/blueprints/PROJECT_BLUEPRINTS_MASTER.md) §6

```
CoGOS (substrate — long horizon)
  └── AAIS (governance spine — LIVE)
        ├── Jarvis (orchestrator / authority)
        ├── Nova (companion — no execution authority)
        ├── Forge (isolated build contractor)
        ├── Immune Protocol + Pattern Ledger
        ├── ARIS (repo intelligence — embedded LIVE; standalone Phase 4)
        ├── Story Forge (narrative engine — execution lanes LIVE)
        └── BeatBox / Speakers (audio — blueprint)
```

**Authority hierarchy:** Jarvis authorizes. Nova may interpret. Forge executes under law.

---

## Where truth lives

| Zone | Path | Role |
|------|------|------|
| Strategy (this doc) | `docs/spine/STRATEGY.md` | Vision → phases → gates |
| Document authority | [`document/`](../../document/README.md) | Blueprints, law, governance, programs |
| Active system map | [`docs/README.md`](../README.md) | Spine, runtime, contracts, proof |
| Implementation | `src/`, `app/`, `aais/`, `governance/` | Governed runtime + genomes |
| Papers / proof corpus | [`docs/proof/discovery/`](../proof/discovery/README.md) | Operator PDFs; proven vs asserted standing |
| Proof-as-you-build | [`MULTI_MODEL_ORCHESTRATION_PATTERN.md`](../architecture/MULTI_MODEL_ORCHESTRATION_PATTERN.md) | Proofs alongside code, not after |

---

## Epistemic standing

Per [REPO_PROOF_LAW.md](../../REPO_PROOF_LAW.md) and multi-model orchestration pattern:

| Standing | Label | Meaning |
|----------|-------|---------|
| 1 | Hypothetical | Speculative or unverified |
| 2 | Asserted | Structured claim without full verification |
| 3 | Proven | Verification-backed |

Outward materials sell **governed intelligence** (proof-backed), not hype or operator narrative inflation.

Discovery corpus (2026-06-08): 32 manifest rows; 13 library-admitted; 8 asserted with explicit `standing_reason`; 19 denied — see [discovery README](../proof/discovery/README.md) and [reconciliation](../proof/discovery/DISCOVERY_ASSERTED_RECONCILIATION_2026-06-08.md).

---

## Phased execution

Each phase has a **gate**, a **papers deliverable**, and a **vision check**.

### Phase 0 — Align (weeks 1–2)

- **Goal:** One strategy chain from Vision → milestones → gates.
- **Deliverable:** This document + linked docs map.
- **Gate:** `make naming-gate`
- **Status:** in progress

### Phase 1 — Stabilize (weeks 2–6)

- **Goal:** Operator product repeatable and governable.
- **Actions:** Golden path ([`OPERATOR_GOLDEN_PATH.md`](../operations/OPERATOR_GOLDEN_PATH.md)), close pilot debt (PLAT-D8 OIDC priority), flagship verification on every meaningful change.
- **Gate:** [`INFINITY_PILOT_BASELINE_CHECKLIST.md`](../baseline/INFINITY_PILOT_BASELINE_CHECKLIST.md)
- **Deliverable:** Proven proof bundle per closed debt item under `docs/proof/platform/`

### Phase 2 — Prove the papers stack (weeks 4–10, parallel)

- **Goal:** Document authority + discovery corpus + proof-as-you-build as one epistemic layer.
- **Actions:** Reconcile discovery manifest; blueprint delta on spec changes; standing labels on all PRs.
- **Gate:** Manifest has no ambiguous asserted rows (each proven or documented deny).
- **Deliverable:** Updated `DISCOVERY_DOCUMENT_MANIFEST.json` + trust bundle refresh

### Phase 3 — Free the operator (weeks 8–14)

- **Goal:** System carries correctness, flow, reference.
- **Actions:** OTEM L10 runbook; daily operator cockpit (3 screens, 3 actions); pattern ledger end-to-end promotion.
- **Gate:** `make infinity1-flagship-verification` green
- **Deliverable:** Workflow skills proof + pattern promotion proof

### Phase 4 — Expand satellites (months 4–9)

| Satellite | Current | Next milestone |
|-----------|---------|----------------|
| Story Forge | Execution live | World-pack + movie lane hardening |
| ARIS | Embedded live | Standalone admission spec → service |
| BeatBox | Blueprint | AudioPlan.json + one voice pipeline proof |
| UGR federation | GA pilot | Close UGR-D5 cross-machine trust |

- **Gate:** Subsystem genome + `make alt*-governed-gate` for touched genes
- **Deliverable:** Per-satellite proof under `docs/proof/` + [`BLUEPRINT_DELTA_CHECKLIST.md`](../../document/compliance/BLUEPRINT_DELTA_CHECKLIST.md)

### Phase 5 — Cog OS substrate (12+ months)

- **Goal:** Blueprint §5.6 Phase 0 glue only (wards/angels, UL-VM wrap, NovaLayer, CLI smoke).
- **Gate:** [`final-promotion-checklist.md`](../../document/governance/final-promotion-checklist.md)
- **Prerequisite:** Phases 1–3 consistently green (OIDC + flagship verification).

---

## Non-goals (explicit)

- Cog OS ISO ship before Phase 5 prerequisites
- Standalone ARIS service before Phase 4 admission spec + proof
- Dreamspace, OTEM execution expansion (blocked per [`SUBSYSTEMS_REMAINING_MAP.md`](../runtime/SUBSYSTEMS_REMAINING_MAP.md))
- Operator data monetization or user-as-commodity business models

---

## Product SKUs (Phase 3 — documentation only)

| SKU | Description |
|-----|-------------|
| Governed runtime seat | AAIS/Jarvis operator tenant (mock → pilot → production) |
| Workflow packs | Plugins and governed workflow families |
| Federation tier | URG cross-instance (optional) |

---

## Operating rhythm

| Cadence | Action |
|---------|--------|
| Monday | Review [`SUBSYSTEMS_REMAINING_MAP.md`](../runtime/SUBSYSTEMS_REMAINING_MAP.md) + pilot debt |
| Daily | Code change ↔ proof packet in same PR |
| Friday | Flagship verification; update discovery manifest if docs changed |
| Monthly | [`INFINITY_PILOT_BASELINE_CHECKLIST.md`](../baseline/INFINITY_PILOT_BASELINE_CHECKLIST.md) review |

---

## Success criteria

| Horizon | Signal |
|---------|--------|
| 30 days | STRATEGY live; golden path documented; flagship verification green on `main` |
| 90 days | PLAT-D8 closed or scoped; discovery manifest reconciled; 3+ co-builder PRs with proven labels |
| 6 months | Story Forge + ARIS milestones with proof; workflow skills in daily use |
| 12 months | Cog OS Phase 0 glue in lab; monetization SKUs tied to product surfaces |

---

## Related docs

- [AAIS_MASTER_SPEC.md](./AAIS_MASTER_SPEC.md) — subsystem ledger
- [STABILIZE_AND_FREE.md](./STABILIZE_AND_FREE.md) — doctrine
- [FIRST_TIME_OPERATOR_GUIDE.md](../operations/FIRST_TIME_OPERATOR_GUIDE.md) — onboarding
- [EARLY_ADOPTER_CHARTER.md](../operations/EARLY_ADOPTER_CHARTER.md) — early adopter terms
- [HELP_WANTED_HUB.md](../community/HELP_WANTED_HUB.md) — co-builder entry
