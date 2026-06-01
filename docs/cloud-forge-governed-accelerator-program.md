# Cloud Forge Governed Accelerator — Program Plan

Status: **Phase 4 complete** — domain slices, priority mapping, session prewarm, tempering dry-run. Program phases 0–4 complete in-repo.

Authority: `META_ARCHITECT_LAWBOOK.md`, `REPO_PROOF_LAW.md`, `document/blueprints/PROJECT_BLUEPRINTS_MASTER.md` (AAIS spine).

## Naming (avoid collision)

| Name | What it is today | This program |
|---|---|---|
| **Wolf-cog Forge** | OS/ISO platform (`docs/forge-platform-gate.md`, Gate G) | Out of scope except shared governance patterns |
| **AAIS Forge contractor** | HTTP bounded diff service (`docs/contracts/FORGE_CONTRACTOR.md`) | Stays contractor; does not govern |
| **Cloud Forge (this doc)** | *Not yet in repo* | Governed cognitive acceleration layer for LLM + tool traffic under AAIS |

## Vision (one sentence)

Snap governed requests onto pre-proven cognition rails (SAFE / NORMAL / EXPRESS) so latency, throughput, and intelligence-per-watt are traded explicitly—without breaking constitutional law or Voss boundaries.

## Constitutional binding

Precedence is fixed:

**Law > Blueprint > Contract > Implementation > Pipeline > Tool**

| Layer | Cloud Forge artifact |
|---|---|
| Law | Meta Architect + Proof Law; admission cannot bypass proof gates |
| Blueprint | `docs/cloud-forge-governed-accelerator-program.md` (this), AAIS master blueprint |
| Contract | `docs/contracts/cloud-forge-rail-contract.md` (Phase 0) |
| Implementation | `src/cloud_forge/` modules (Phase 1+) |
| Pipeline | Integration with `governed_direct_pipeline`, Jarvis operator |
| Tool | LLM gateways, caches, K8s priority (Phase 3+, optional) |

**Rule:** Express rail is a *performance* class, not a *permission* class. Law sets the ceiling; rails choose speed inside the ceiling.

## What already exists (proven / asserted in repo)

| Asset | Location | Reuse |
|---|---|---|
| Governed packet pipeline + `express` intent | `src/governed_direct_pipeline.py` | Rail outcomes emit as packet traces |
| Immune protocol | `src/immune_protocol.py` | Risk elevation → force SAFE rail |
| Voss cycle binding Λ | `voss_binding.py` | Post-mutation boundary; rail transitions log here |
| Lane guardrails (Jarvis ↔ Forge) | `src/jarvis_operator.py` | Pattern for lane arbitration |
| L0 tool cache (in-process) | `app/tools.py` | Seed for L0 deterministic cache contract |
| Pattern Ledger (concept) | `PROJECT_BLUEPRINTS_MASTER.md` | Target store for rail decisions + outcomes |
| Forgekeeper governance model | `FORGEKEEPER_BLUEPRINT.md` | Claim labels + proof linkage pattern |
| Platform Gate G | `docs/forge-platform-gate.md` | Governance CI discipline; not cognitive rails |

## Target architecture

```mermaid
flowchart TB
  subgraph admission [Admission - Law]
    LAW[META_ARCHITECT + Proof Law]
    ENV[law_envelope per tenant/task]
  end
  subgraph scheduler [Rail Scheduler - Blueprint/Contract]
    SIG[task_signature + risk + novelty]
    CHOOSE[choose_rail SAFE|NORMAL|EXPRESS]
    PLAN[build_plan CognitionPlan]
  end
  subgraph runtime [Runtime - Implementation]
    VOSS[Voss Λ + capability masks]
    PIPE[governed_direct_pipeline]
    CACHE[L0-L2 caches scoped by tenant+law]
  end
  subgraph obs [Observation]
    LEDGER[Pattern Ledger entries]
    PROOF[Trust / proof bundles]
  end
  LAW --> ENV --> SIG --> CHOOSE --> PLAN --> VOSS --> PIPE
  PLAN --> CACHE
  CHOOSE --> LEDGER
  PIPE --> LEDGER --> PROOF
```

## Performance vector (multi-objective)

Per tenant/app, store a **PerformanceProfile**:

```json
{
  "latency_bias": 0.4,
  "throughput_bias": 0.3,
  "intelligence_bias": 0.3
}
```

Per actor, store **governance weight vector** (Phase 1: scalar `wL` only; Phase 2: full `wL`, `wT`, `wI`):

```json
{
  "wL": 120,
  "wT": 80,
  "wI": 200,
  "tier": "A"
}
```

Scheduler inputs: `(task, actor, tenant, cluster_state, law_envelope)` → `(rail, model_tier, parallelism, cache_mode, speculation)`.

## Rail definitions (v1)

| Rail | Step chain (cognition) | Verification | Cache | Who may ride |
|---|---|---|---|---|
| **SAFE** | ANALYZE → PLAN → TOOLS → DRAFT → CRITIQUE → FINAL | Full | Minimal | All; forced when risk HIGH |
| **NORMAL** | PLAN → TOOLS → DRAFT → FINAL | Standard | Moderate | Default |
| **EXPRESS** | PLAN+TOOLS → FINAL | Sampled + stream gate | Aggressive | High `wL` + LOW risk + law allows |

Domain-specific EXPRESS templates (e.g. Forge/Voss/OS architecture Q&A) are Phase 2 backlog items.

## Risk estimation (v1 rules, no ML)

`estimate_risk(task, law_envelope)` — rule table:

| Signal | Risk |
|---|---|
| PII / credentials / prod mutation / constitutional edit | HIGH → SAFE only |
| External side effects / tool execution / repo write | MEDIUM → NORMAL max |
| Docs / explanation / read-only retrieval | LOW → EXPRESS allowed if weight permits |

`estimate_novelty(task, pattern_cache)` — Phase 1: always MEDIUM; Phase 2: hash match against Pattern Ledger.

## Phased delivery

### Phase 0 — Governance artifacts (no runtime speed claims) — **COMPLETE**

**Goal:** Lawful scaffolding only.

| ID | Deliverable | Status |
|---|---|---|
| C0-1 | This program doc | **COMPLETE** |
| C0-2 | Rail contract `docs/contracts/cloud-forge-rail-contract.md` | **COMPLETE** |
| C0-3 | Failsafe doc `docs/failsafe/cloud-forge-rail-failsafe.md` | **COMPLETE** |
| C0-4 | `docs/cloud-forge-backlog.md` | **COMPLETE** |
| C0-5 | Blueprint cross-link `PROJECT_BLUEPRINTS_MASTER.md` §1.6 | **COMPLETE** |
| C0-6 | Contracts README entry | **COMPLETE** |
| C0-7 | Proof packet `docs/proof/cloud-forge/C0_PHASE0_PROOF.md` | **COMPLETE** |

**Verification:** Structural (files present). Claim **asserted** per C0 proof packet; scheduler **proven** only after Phase 1 tests.

### Phase 1 — Rail scheduler library (local, in-process) — **COMPLETE**

**Goal:** `choose_rail` + `build_plan` as pure functions with tests; no cloud yet.

| ID | Deliverable | Status |
|---|---|---|
| C1-1 | `src/cloud_forge/types.py` | **COMPLETE** |
| C1-2 | `src/cloud_forge/risk.py` | **COMPLETE** |
| C1-3 | `src/cloud_forge/rails.py` | **COMPLETE** |
| C1-4 | `tests/test_cloud_forge_rails.py` | **COMPLETE** (20 tests) |
| C1-5 | Pipeline hook `cloud_forge_context` | **COMPLETE** |
| C1-6 | Proof `docs/proof/cloud-forge/C1_RAIL_SCHEDULER_PROOF.md` | **COMPLETE** |

**Verification:** `py -3.12 -m unittest tests.test_cloud_forge_rails -v` — **proven** per C1 proof packet.

### Phase 2 — Observation + Pattern Ledger wiring — **COMPLETE**

**Goal:** Every rail choice logged for learning; no auto-promotion without verification gate.

| ID | Deliverable | Status |
|---|---|---|
| C2-1 | Ledger adapter `src/cloud_forge/ledger.py` | **COMPLETE** |
| C2-2 | Promotion stub `src/cloud_forge/promotion.py` | **COMPLETE** |
| C2-3 | EXPRESS template `forge/voss/os_architecture` | **COMPLETE** |
| C2-4 | Jarvis readout + `metadata.cloud_forge_context` | **COMPLETE** |
| C2-6 | Proof `docs/proof/cloud-forge/C2_OBSERVATION_PROOF.md` | **COMPLETE** |

**Verification:** `py -3.12 -m unittest tests.test_cloud_forge_rails tests.test_cloud_forge_phase2 -v`

### Phase 3 — Caches (law-scoped) — **COMPLETE**

| ID | Layer | Status |
|---|---|---|
| C3-1 | L0 deterministic tools (tenant+law) | **COMPLETE** — `src/cloud_forge/cache.py`, `app/tools.py` bridge |
| C3-2 | L1 answer cache | **COMPLETE** |
| C3-3 | L2 CognitionPlan cache | **COMPLETE** |
| C3-5 | Proof `docs/proof/cloud-forge/C3_CACHE_PROOF.md` | **COMPLETE** |

**Verification:** `py -3.12 -m unittest tests.test_cloud_forge_rails tests.test_cloud_forge_phase2 tests.test_cloud_forge_phase3 -v`

Governance: no cross-tenant keys; `law_version` mismatch → miss; `forbid_cache_above` caps mode before resolve.

### Phase 4 — Cloud locality — **COMPLETE**

| ID | Deliverable | Status |
|---|---|---|
| C4-1 | Domain slice layout + `configs/cloud-forge/domain-slices.json` | **COMPLETE** |
| C4-2 | `map_governance_to_priority()` | **COMPLETE** |
| C4-3 | `SessionPrewarmStore` | **COMPLETE** |
| C4-4 | `src/cloud_forge/tempering.py` + job doc | **COMPLETE** |
| C4-5 | Proof `docs/proof/cloud-forge/C4_LOCALITY_PROOF.md` | **COMPLETE** |

**Claim discipline:** p95 latency improvements remain **asserted** until cross-machine benchmarks (CF-D5).

## Pseudocode (contract reference)

```python
def choose_rail(task, actor, tenant, cluster, law_envelope) -> Rail:
    risk = estimate_risk(task, law_envelope)
    if risk == HIGH:
        return SAFE
    rail = NORMAL if risk == MEDIUM else EXPRESS
    if actor.wL >= tenant.wL_express_threshold and tenant.latency_bias >= 0.35 and risk != HIGH:
        rail = min(rail, EXPRESS)  # faster
    if actor.wL < tenant.wL_express_floor:
        rail = max(rail, NORMAL)  # never EXPRESS
    return rail


def build_plan(task, rail, actor, tenant, cluster) -> CognitionPlan:
    steps = RAIL_STEP_CHAINS[rail]
    return CognitionPlan(
        steps=steps,
        model_tier=select_model(task, rail, actor, tenant, cluster),
        parallelism=select_parallelism(rail, actor.wT, cluster),
        cache_mode=select_cache_mode(rail, actor.wI, tenant),
        speculation=select_speculation(rail, actor.wL, cluster),
    )
```

## What we need to do (ordered checklist)

1. **Approve Phase 0 scope** — Meta Architect / operator OK on naming and AAIS placement.
2. **Write rail contract** (C0-2) — machine-readable schemas + violation codes.
3. **Write failsafe doc** (C0-3) — global FORCE_SAFE, cache poison handling.
4. **Implement Phase 1 library** (C1-1–C1-5) — smallest code that proves rail logic.
5. **Hook governed_direct_pipeline** — attach `rail_decision` to traces (read-only metadata first).
6. **Proof bundle** — `docs/proof/cloud-forge/C1_RAIL_SCHEDULER_PROOF.md` after tests green.
7. **Phase 2 ledger** — only after C1 is proven.
8. **Defer Phase 4 cloud** until cognitive rails are proven locally.

## Explicit non-goals (v1)

- No valuation or market claims in repo docs.
- No bypass of Forgekeeper / governance CI gates.
- No EXPRESS for constitutional edits, proof law changes, or destructive ops.
- No multi-tenant cache without law-scoped keys in contract.
- No replacement of Wolf-cog Forge ISO pipeline.

## Open decisions (need operator input)

| # | Question | Default if silent |
|---|---|---|
| D1 | Separate backlog file vs `docs/forge-backlog.md` section? | New `docs/cloud-forge-backlog.md` |
| D2 | Phase 1 integration point: pipeline only vs Jarvis operator first? | Pipeline metadata first |
| D3 | Pattern Ledger storage: new JSONL vs extend existing proof index? | `docs/proof/cloud-forge/rail-decisions.jsonl` |
| D4 | First EXPRESS domain template? | `forge/voss/os_architecture` |

## Debt register (initial)

| ID | Gap | Severity | Owner |
|---|---|---|---|
| CF-D1 | No `cloud-forge-rail-contract.md` | High | **CLOSED** (C0-2) |
| CF-D2 | No rail scheduler implementation | High | **CLOSED** (C1) |
| CF-D3 | Pattern Ledger not wired for rails | Medium | **CLOSED** (C2) |
| CF-D4 | Cloud co-location / K8s priority unproven | Low | **CLOSED** (C4) |
| CF-D5 | Cross-machine latency benchmarks | Medium | Post Phase 1 |

## Success metrics (proof-gated)

| Metric | Target (asserted until measured) | Proof required |
|---|---|---|
| Rail decision latency overhead | < 5 ms in-process | Unit test + timing log |
| EXPRESS eligibility accuracy | 0 constitutional bypasses in test suite | Adversarial tests |
| Repeat-task speedup | 5×–20× step reduction on fixture patterns | Before/after trace comparison |
| p95 user-visible latency | TBD per domain | Cross-machine Trust Bundle |

---

*Program phases 0–4 complete. Optional follow-up: CF-D5 cross-machine latency benchmarks + live K8s deploy.*
