# Nova Capability Inventory

**Living checklist** for Nova Cortex, companion surfaces, and cognitive integration inside AAIS/Jarvis.

| Field | Value |
|-------|-------|
| **Family** | Nova Cortex v3.0 — Persistent Narrative Continuity |
| **Family ID** | `nova.cortex` |
| **Authority** | Tri-Core (Nova interprets; Jarvis authorizes) |
| **Last reviewed** | 2026-06-17 |

Update this document whenever behavior changes (change-of-reality). Link proof in [docs/proof/cognitive_runtime/](../proof/cognitive_runtime/).

**Doctrine:** [STAGE2_COPILOT_DOCTRINE.md](./STAGE2_COPILOT_DOCTRINE.md) — Stage 1 (Thought) · Stage 2 (Copilot integrator) · Stage 3 (Environment).

**Claim labels:** `proven` · `asserted` · `debt` · `by-design`

---

## How to verify (one-click)

```bash
pytest tests/test_nova_formal_spec.py tests/test_coherence_projection.py tests/test_intent_agency_evidence.py tests/test_intent_core.py tests/test_intent_store.py tests/test_narrative_runtime.py tests/test_narrative_store.py tests/test_narrative_continuity_proof.py tests/test_integration_cog_runtimes.py tests/test_capability_governance.py -q
python .github/scripts/check-nova-cortex-governance.py
python .github/scripts/check-nova-narrative-continuity.py
python .github/scripts/check-nova-intent-agency.py
make ai-factory-gate
make slingshot-gate
```

---

## Stack (what runs, in order)

- [x] **Spine** — doctrine envelope (`aais_composed_runtime`) — `asserted`
- [x] **ARIS** — admission / non-copy gate — `asserted`
- [x] **Jarvis** — routing, tools, provider pick, finalization — `asserted`
- [x] **Nova Face** — companion surface binding — `asserted`
- [x] **Nova Cortex** — lobes + ledger — `asserted`
- [x] **Intent Core** — commitments, tensions, closure — `proven` (single-machine)
- [x] **Narrative** — continuity-of-self — `proven` (single-machine)
- [x] **Coherence Projection** — mind → voice context inject — `asserted`
- [x] **Provider LLM** — local or cloud generation slot — `asserted`
- [x] **Speaking Runtime** — listen/frame/plan/speak/check wrap — `asserted`
- [x] **AI Factory v1** — spec → spine → runtime → proof → envelope — `asserted` · see [AI_FACTORY.md](./AI_FACTORY.md)
- [x] **AI Factory v1.1 Wolf deploy** — build → wolf payload promotion — `asserted` (single-machine) · `ai_factory deploy --wolf`
- [x] **AI Slingshot v1** — Mechanic preload → Nova fast-path burst lane — `asserted` · see [AI_SLINGSHOT.md](./AI_SLINGSHOT.md)

Docs: [NOVA_CORTEX.md](./NOVA_CORTEX.md) · [NOVA_CORTEX_FORMAL_SPEC.md](./NOVA_CORTEX_FORMAL_SPEC.md) · [NOVA_INTENT_CORE.md](./NOVA_INTENT_CORE.md) · [NOVA_NARRATIVE.md](./NOVA_NARRATIVE.md) · [NOVA_COHERENCE_PROJECTION.md](./NOVA_COHERENCE_PROJECTION.md) · [AI_FACTORY.md](./AI_FACTORY.md) · [AI_SLINGSHOT.md](./AI_SLINGSHOT.md) · [NOVA_LAWFUL_PRODUCTIZATION.md](./NOVA_LAWFUL_PRODUCTIZATION.md)

---

## 1. Turn orchestration

| Capability | Status | Notes |
|------------|--------|-------|
| Lobe router per turn | `asserted` | `nova_cognitive_router()` |
| Full cortex on companion / cognitive-enabled turns | `asserted` | `configure_nova_cognitive_turn()` |
| Cortex fast path (Attention + Reasoning only) | `asserted` | `cortex_fast_path` |
| AI Slingshot burst lane (customer workflow preload → fast compose) | `asserted` | `slingshot/` + chat `slingshot` payload |
| Composed turn: Spine → ARIS → Nova bridge | `asserted` | `run_composed_turn()` |
| ARIS block before cortex | `asserted` | Returns 403 when blocked |
| Cortex runs **before** LLM; Speaking wraps **after** | `asserted` | `api.py` chat pipeline |
| Append-only shared cognitive ledger | `asserted` | Per-turn stage records |
| Formal ledger schema + compression/retention | `asserted` | [NOVA_CORTEX_FORMAL_SPEC.md](./NOVA_CORTEX_FORMAL_SPEC.md) §2 |
| Decidable activation predicates φ | `asserted` | `src/cog_runtime/formal/activation_predicates.py` |
| Output verify + bounded constraints | `asserted` | `verify_reply()` + `output_constraints.py` |
| Intent–narrative turn reconciliation | `asserted` | `reconcile_intent_narrative()` |
| Theorem 5.1 artifact-only typing (CI) | `asserted` | `check-nova-cortex-governance.py` |
| Spine halt-on-false pipeline | `asserted` | `formal/spine_pipeline.py` |
| Agency preservation theorem (full proof) | `debt` | Runtime check **asserted** — `agency_preservation.py` |
| Distributed ledger monotonicity | `debt` | Merge sketch **asserted** — `distributed_ledger.py` |
| Live LLM rejection sampling | `asserted` | `run_generation_with_verification()` in chat path |
| Family spec + Wolf manifest export | `proven` | Governance gate |

- [x] Turn pipeline wired in live chat
- [x] INV-1 harness (single-machine reboot round-trip) — `asserted` · `tests/test_wolf_rehydration_harness.py`
- [ ] Cross-machine turn pipeline proof — `debt`

---

## 2. Cognitive lobes (8 registered)

Each lobe requires `capability_metric`, `baseline_substitute`, `evidence_status`, `sunset_trigger` — see [capability_governance.py](../../src/cog_runtime/capability_governance.py).

### `jarvis.reasoning` — executive

- [x] OODA / reasoning packet for governed paths — `asserted`
- [x] Constitutional executive (not sunset) — `by-design`

### `speaking.runtime` v1.0 — speech loop

- [x] Stages: listen, frame, plan, speak, check, (update) — `asserted`
- [x] Frame kinds (question, design, decision, …) — `asserted`
- [x] `validate_reply()` on wrapped output — `asserted`
- [x] `nova_speaking_adapter()` wraps LLM body — `asserted`

### `cognitive.attention` v1.2

- [x] `focus_artifact`: primary, secondary, salience, weights — `asserted`
- [x] Feeds deliberation, reflection, planning — `asserted`

### `cognitive.memory` v1.2

- [x] encode → index → retrieve → forget — `asserted`
- [x] Memory board cues + face scope — `asserted`
- [x] Episodic compression to session metadata — `asserted`

### `cognitive.deliberation` v1.2

- [x] Activates on decision frames — `asserted`
- [x] options → tradeoffs → commit → revisit — `asserted`
- [x] Multi-criteria scores incl. `intent_alignment` — `asserted`
- [x] Deterministic commit (default) — `asserted`
- [x] Optional LLM deliberation (JSON decision) — `asserted`
- [x] `intent_influence` on decision object — `asserted`

### `cognitive.reflection` v1.3

- [x] Alignment: aligned / partial / misaligned — `asserted`
- [x] Gaps, adjustments, next-turn hints — `asserted`
- [x] Handoff to planning on companion / gaps — `asserted`
- [x] Post-reply merge with speak body — `asserted`

### `cognitive.planning` v1.3

- [x] Bounded steps + step chains (primary, continuation, subgoal) — `asserted`
- [x] Adaptive chain selection — `asserted`
- [x] Intent-weighted chain scoring — `asserted`
- [x] Honor active commitments in steps — `asserted`
- [x] `next_action`, `intent_influence` — `asserted`

### `cognitive.execution` v1.2

- [x] bind → verify → recover → rollback — `asserted`
- [x] Verification vs focus / planned action — `asserted`
- [x] Safe rollback policy — `asserted`
- [x] Resolve commitments on execution complete — `asserted`

**Lobe A/B sunset proof (beat baseline × 3 cycles):** — `debt` for all lobes except where noted below

---

## 3. Cortex modules (not lobes)

### Multi-turn arcs (`cortex.arcs` v1.3)

- [x] Goal types: decision, continuity, exploration, repair, general — `asserted`
- [x] Root goal, subgoals, hierarchy, open threads — `asserted`
- [x] Parent/child goal closure on execution — `asserted`
- [x] Persist `cortex_arc` on session — `asserted`

### Self-tuning (`cortex.tuning` v1.1)

- [x] Threshold adjustment from execution/reflection — `asserted`
- [x] Drift guard + bounded history — `asserted`

### Nova Narrative (`nova.narrative` v1.0)

- [x] active_story, becoming, working_on, chapter, threads, promises, growth — `proven`
- [x] Fixed core_identity + identity drift guard — `proven`
- [x] `continuity_answers` (doing / done / toward) — `proven`
- [x] `intent_report` + tension in becoming — `proven`
- [x] Observe-only (not authority) — `by-design`
- [ ] Multi-turn session-reset narrative fixture (3+ turns) — `debt`
- [ ] Operator continuity rubric study — `debt`
- [ ] Wolf metal reboot same story — `debt`

Proof: [NARRATIVE_V1_PROOF_BUNDLE.md](../proof/cognitive_runtime/NARRATIVE_V1_PROOF_BUNDLE.md) · Plan: [NARRATIVE_CONTINUITY_EVIDENCE_PLAN.md](../proof/cognitive_runtime/NARRATIVE_CONTINUITY_EVIDENCE_PLAN.md)

### Nova Intent Core (`nova.intent` v0.2)

- [x] Commitments, tensions, horizon goals, protected values — `proven`
- [x] Conflict + deferral + in_tension — `proven`
- [x] Unified closure (arc / execution / intent) — `proven`
- [x] Claim posture per commitment — `proven`
- [x] Deliberation + Planning consult prior intent — `proven`
- [x] Commitments survive story change (fixture) — `proven`
- [x] Consult-only (not authority) — `by-design`
- [ ] Wolf metal reboot same commitments — `debt`
- [ ] Operator “speaks from commitments” rubric — `debt`

Proof: [INTENT_AGENCY_V1_PROOF_BUNDLE.md](../proof/cognitive_runtime/INTENT_AGENCY_V1_PROOF_BUNDLE.md)

### Coherence Projection v1.0 (integration, not a lobe)

- [x] `build_coherence_projection()` from session metadata — `asserted`
- [x] `NovaCoherenceProjectionModule` → provider `cognitive` channel — `asserted`
- [x] Injected before `generate_chat` when cortex enabled — `asserted`
- [x] Read-only, bounded, no chain-of-thought dump — `by-design`
- [ ] Operator-visible coherence from projection — `debt`

Doc: [NOVA_COHERENCE_PROJECTION.md](./NOVA_COHERENCE_PROJECTION.md)

---

## 4. Persistence & rehydration

| Store | Dev path | Wolf path | Status |
|-------|----------|-----------|--------|
| Narrative | `.runtime/nova_narrative/{id}.json` | `/opt/cogos/memory/operator/nova_narrative/` | `proven` (single-machine) |
| Intent | `.runtime/nova_intent/{id}.intent.json` | `/opt/cogos/memory/operator/nova_intent/` | `proven` (single-machine) |

- [x] Save / load / flush / rehydrate (narrative) — `proven`
- [x] Save / load / flush / rehydrate (intent) — `proven`
- [x] Boot hooks: `rehydrate_nova_*_boot()`, `seed_session_nova_*()` — `proven`
- [ ] Cross-machine wolf reboot proof bundles — `debt`

---

## 5. Nova Face & companion lanes

| Surface | Lane | Status |
|---------|------|--------|
| Tiny Nova | minimal companion | `asserted` |
| Small Nova | calm companion | `asserted` |
| Super Nova | deep companion (gated) | `asserted` |
| Jarvis | operator / control | `asserted` |

- [x] `bridge_nova_face_to_cortex_and_jarvis()` — `asserted`
- [x] Companion defaults: cognitive + narrative + intent persist — `asserted`
- [x] Optional deliberation LLM on companion — `asserted`

---

## 6. LLM integration

| Slot | Local | Cloud | Status |
|------|-------|-------|--------|
| Main reply | `LocalProvider` → `generate_chat` | OpenRouter, Claude, … | `asserted` |
| Deliberation (optional) | provider registry | same | `asserted` |
| Coherence context | modular preview | same | `asserted` |

- [x] Provider routing via `preferred_provider` / `model_route` — `asserted`
- [x] Projection in modular pipeline — `asserted`
- [ ] Prove replies materially use projected state in chat — `debt`

---

## 7. Governance CI

| Gate | Script | Status |
|------|--------|--------|
| Lobe capability matrix | `check-nova-cortex-governance.py` | `proven` |
| Narrative continuity | `check-nova-narrative-continuity.py` | `proven` |
| Intent agency | `check-nova-intent-agency.py` | `proven` |

Workflows: `.github/workflows/nova-cortex-governance-gate.yml`, `nova-narrative-continuity-gate.yml`, `nova-intent-agency-gate.yml`

---

## 8. Wolf CoG OS readiness

- [x] Store dir placeholders (`nova_narrative/`, `nova_intent/`) — `asserted`
- [x] `cognitive_runtime_family.json` in payload — `asserted`
- [x] `cogos_runtime_bridge.py` spec / validate / rehydrate — `asserted`
- [ ] Metal install proof checklist complete — `debt` · see [METAL_PROOF_CHECKLIST.md](../../cog-os/docs/METAL_PROOF_CHECKLIST.md)

---

## 9. Explicit non-goals (by design)

- [ ] Narrative or Intent route tools or authorize actions — **must not** (`by-design`)
- [ ] Narrative redefine core identity — **blocked** by guard (`by-design`)
- [ ] Cortex compete with Jarvis for control — **blocked** (`by-design`)
- [ ] Raw chain-of-thought in user output — **blocked** (`by-design`)
- [ ] UGR LLM lane replace Nova companion pipeline — **separate system** (`by-design`)

---

## 10. Mind map (current abilities)

```text
UNDERSTAND     Attention, Memory cues, frame kind
DECIDE         Deliberation (+ optional LLM), criteria + intent alignment
ALIGN          Reflection → Planning → Execution verify
CONTINUE       Arcs, Narrative, Intent stores
ADAPT          Self-tuning thresholds
SPEAK FROM     Coherence projection → LLM → Speaking wrap
GOVERN         Capability matrix, identity guard, ARIS, Jarvis
```

---

## Debt register (inventory-specific)

| ID | Item | Severity | Owner | Target |
|----|------|----------|-------|--------|
| INV-1 | Wolf metal reboot narrative + intent rehydration | high | ops | cross-machine proof bundle · **asserted harness landed** |
| INV-2 | Operator continuity rubric (narrative) | medium | ops | human study + proof |
| INV-3 | Operator coherence rubric (projection) | medium | ops | paired chat fixture |
| INV-4 | Multi-turn narrative session-reset harness | medium | eng | pytest + proof bundle |
| INV-5 | Per-lobe A/B sunset evidence (×3 cycles) | low | eng | staged proof cycles |
| INV-6 | Stage 2 evaluation metrics (fidelity, distortion, leakage) | medium | eng | `src/stage2_fidelity_metrics.py` + CI gate · **asserted fixtures** |
| INV-7 | Consentful inference enforcement in deliberation defaults | medium | eng | doctrine `consentful_inference` |
| INV-8 | AI Factory cross-machine build replay | medium | eng | Wolf deploy v1.1 **asserted** single-machine |
| INV-9 | Lab Console cross-machine worktree replay + Stage 2 coding-agent fidelity metrics | medium | eng | Lab↔Forge bridge + session `stage2_metrics` · **asserted** |
| PLAT-D1 | Unified platform ingress (`platform/` :8090) | medium | platform | **asserted** v1 · [PLATFORM_MEMBRANE.md](./PLATFORM_MEMBRANE.md) |
| PLAT-D2 | Org RBAC + API keys (SSO deferred PLAT-D8) | medium | platform | **asserted** v1 |
| PLAT-D3 | Global job registry + subsystem adapters | low | platform | **asserted** v1 |
| PLAT-D4 | Federated artifact index | low | platform | **asserted** v1 |
| PLAT-D5 | Platform operator console `/platform` | low | platform | **asserted** v1 |
| PLAT-D6 | Deploy organism (compose + Helm skeleton) | medium | ops | **asserted** v1 |
| PLAT-D7 | Cross-machine platform proof fleet | medium | ops | manifest **active**; `proof_required` + worker hook **asserted**; hash **proven** pending CI consensus |
| PLAT-D8 | OIDC per org | medium | platform | Google/Microsoft/GitHub registry + Bearer session **asserted** |
| PLAT-D9 | Multi-region queues + artifact prefixes | medium | platform | region-scoped Redis + `PLATFORM_WORKER_REGION` **asserted** |
| PLAT-D10 | Drift-as-jobs (`drift_check` / `drift_investigation`) | medium | platform | detectors + console drift queue **asserted** |
| PLAT-D11 | Read-only platform assistant | low | platform | `POST /v1/assistant/query` + `/platform/assistant` **asserted** |
| PLAT-D12 | Org policy DSL | medium | platform | `PUT /v1/orgs/{id}/policies` + admission **asserted** |
| PLAT-D13 | Org billing gate | medium | platform | `billing_status` + engine before admission **asserted** |
| PLAT-D14 | Workflow DAG (`workflow_run`) | medium | platform | CRUD/run API + `/platform/workflows` **asserted** |
| PLAT-D15 | Operator Mesh (presence, assign, on-call, handoff) | medium | platform | `/platform/mesh` **asserted** |
| PLAT-D16 | Workflow Marketplace (org/tenant/curated) | medium | platform | `/platform/marketplace` **asserted** |
| PLAT-D17 | Proof Federation (k-of-n attestations) | medium | ops | v25–v28 signed attestations + dispute→drift; CI quorum **proven** via `platform-cross-machine-gate` tertiary |
| PLAT-D18 | Membrane v3 spec pack | low | docs | **proven** — `check-platform-v3-spec-governance.py` |
| PLAT-D19 | Operator Mesh v2 (SSE, policy) | low | ops | **asserted** — `PLATFORM_V21_V22_PROOF_BUNDLE.md` |
| PLAT-D20 | Marketplace v2 (lifecycle, analytics) | low | ops | **asserted** — `PLATFORM_V23_V24_PROOF_BUNDLE.md` |
| PLAT-D21 | Proof Federation v2 | medium | ops | **asserted** local; CI **proven** at v28 gate |
| PLAT-D22 | Sovereign control plane (exports, tenant summary) | low | ops | **asserted** — `PLATFORM_V29_V30_PROOF_BUNDLE.md` |
| PLAT-D23 | Membrane v4 spec pack | low | docs | **proven** — `check-platform-v4-spec-governance.py` |
| PLAT-D24 | Proof Federation v3 (Ed25519, bundles, replay v3) | medium | ops | **asserted** local; CI **proven** at v36 gate |
| PLAT-D25 | Event membrane (webhooks v31–v32) | low | ops | **asserted** — `PLATFORM_V31_V32_PROOF_BUNDLE.md` |
| PLAT-D26 | Marketplace v3 (reviews, catalog) | low | ops | **asserted** — `PLATFORM_V33_V34_PROOF_BUNDLE.md` |
| PLAT-D27 | Operator Mesh v3 (retention, queue) | low | ops | **asserted** — `PLATFORM_V37_V38_PROOF_BUNDLE.md` |
| PLAT-D28 | Sovereign v2 (compliance policy, bounded exports) | low | ops | **asserted** — `PLATFORM_V39_V40_PROOF_BUNDLE.md` |
| PLAT-D29 | Membrane v5 spec pack (Sixth arc) | low | docs | **proven** — `check-platform-v5-spec-governance.py` |
| PLAT-D30 | Autonomous Org Mesh (v41–v42) | medium | platform | **asserted** — `PLATFORM_V41_V42_PROOF_BUNDLE.md` |
| PLAT-D31 | Global Proof Network (v43–v44) | medium | ops | **proven** local + tertiary script; record CI URL in `PLATFORM_V43_V44_PROOF_BUNDLE.md` |
| PLAT-D32 | Inter-Membrane Exchange IMXP (v45–v46) | medium | platform | **asserted** — `PLATFORM_V45_V46_PROOF_BUNDLE.md` |
| PLAT-D33 | Platform Ledger v2 (v47–v48) | low | platform | **asserted** — `PLATFORM_V47_V48_PROOF_BUNDLE.md` |
| PLAT-D34 | Sovereign Runtime (v49–v50) | low | ops | **asserted** — `PLATFORM_V49_V50_PROOF_BUNDLE.md` |
| PLAT-PILOT-D1 | Infinity Pilot K8s multi-tenant hardening | high | ops | **proven** — PLATFORM_K8S_ISOLATION_PROOF |
| PLAT-PILOT-D2 | Infinity Pilot deploy compose smoke | medium | ops | **asserted** — `PLATFORM_PILOT_DEPLOY_PROOF_BUNDLE.md`, `scripts/pilot_compose_smoke.py` |
| UGR-D9 | UGR Ledger Bridge v1 | medium | runtime | **asserted** — `UGR_LEDGER_BRIDGE_V1_PROOF_BUNDLE.md` |
| NOVA-PROD-D1 | Local Lawful Nova CLI/API productization | medium | runtime | **proven local** — `nova-productization-gate`; see `NOVA_LAWFUL_PRODUCTIZATION.md` |

---

## Change log

| Date | Change |
|------|--------|
| 2026-05-30 | Initial living inventory: v3.0 stack, Intent v0.2, Coherence Projection v1.0 |
| 2026-05-31 | AI Factory v1 POC: governed build pipeline (`asserted`) |
| 2026-05-31 | Stack closure: INV-1 harness, memory membrane, AI Factory Wolf deploy, INV-6 metrics, Lab↔Forge bridge |
| 2026-05-31 | Platform Membrane v1: ingress, jobs, artifacts, `/platform` UI, PLAT-D1..D7 |
| 2026-05-31 | Platform v1.1–v7: scopes/RBAC, policy, invites, billing export, job graph, artifact explorer, proof runner |

When shipping behavior changes, update checkboxes, claim labels, debt register, and link a proof bundle.
