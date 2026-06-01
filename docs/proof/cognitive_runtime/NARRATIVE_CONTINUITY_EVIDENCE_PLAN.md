# Narrative Continuity — Evidence Plan

**Purpose:** Prove that Narrative improves continuity, reduces context loss, and helps operators feel they are **continuing a conversation** rather than restarting every turn.

**Status:** Automated A/B fixture **proven** ([NARRATIVE_V1_PROOF_BUNDLE.md](./NARRATIVE_V1_PROOF_BUNDLE.md)). Human and cross-session operator evidence **pending**.

This is the next focus — **not** adding runtimes.

## What is already proven (single-machine)

| Signal | Method | Result |
|--------|--------|--------|
| Three continuity questions answered | `continuity_answers` + pytest | **proven** |
| Treatment beats arc+planning baseline on `done` | `compare_continuity_treatment_vs_baseline()` | **proven** |
| Session-boundary persistence | `test_cross_session_rehydration` | **proven** |
| Boot rehydration API | `rehydrate_nova_narrative_boot()` | **proven** |
| Identity guard | `identity_consistency` invariant | **proven** |

## What must be proven next

### 1. Continuity improvement (quantitative)

**Hypothesis:** Companion turns with Narrative persistence score higher on continuity completeness than the same turns without Narrative store rehydration.

| Metric | Definition | Baseline | Target |
|--------|------------|----------|--------|
| `continuity_score` | Fraction of doing/done/toward filled | Arc+planning only (~0.67 on fixture) | Narrative ≥ 1.0 on same fixture |
| `story_persistence_rate` | Same `active_story` after simulated session boundary | 0% without store | 100% with store |
| `thread_retention` | Open threads carried across session boundary | Message window only | Narrative store |

**Verification path:**

```bash
pytest tests/test_narrative_store.py tests/test_narrative_continuity_proof.py -q
python .github/scripts/check-nova-narrative-continuity.py
```

### 2. Context loss reduction (structural)

**Hypothesis:** Narrative reduces loss of operator-stated goals and promises across companion multi-turn fixtures.

| Metric | How measured |
|--------|----------------|
| `promise_survival` | Promises in turn N still present or closed in turn N+k |
| `chapter_coherence` | `current_chapter` does not reset to generic text mid-arc |
| `growth_chain` | `last_growth` references prior turn execution/reflection |

**Fixture debt:** Add multi-turn companion pytest harness (3+ turns, simulated session reset between turns 2 and 3).

### 3. Operator-perceived continuity (qualitative)

**Hypothesis:** Operators report higher "continuing a conversation" vs "starting over" when Narrative persistence is enabled.

| Method | Pass criterion |
|--------|----------------|
| Paired companion script (same user goal, with/without `nova_narrative_persist`) | Majority prefer persist arm on continuity rubric |
| Rubric dimensions | Story remembered, threads not dropped, no jarring reset |

**Status:** **debt** — requires human operator study; not substitutable by pytest alone.

### 4. Cross-machine wolf boot (platform)

**Hypothesis:** After wolf-cog-os-full reboot, `/opt/cogos/memory/operator/nova_narrative/{id}.json` rehydrates the same `active_story`.

**Status:** **debt** — see [NOVA_CORTEX_V3_ROADMAP.md](../../docs/runtime/NOVA_CORTEX_V3_ROADMAP.md).

## Claim ladder

| Stage | Label | Requirement |
|-------|-------|-------------|
| Schema + invariant | canonical | Docs + `observe_only` + `identity_consistency` |
| Automated fixture | **proven** | Current pytest + continuity gate |
| Multi-turn session reset fixture | asserted → proven | New test harness |
| Operator rubric study | proven | Human evidence + proof bundle |
| Wolf metal reboot | proven | Cross-machine proof bundle |

## Non-goals

- Adding cognition lobes to improve continuity
- Treating Narrative as authority or routing plane
- Conflating continuity with consciousness or "spark" claims without operator evidence

## Why this matters

The v3.0 milestone **Persistent Narrative Continuity** is not "another lobe." It is the moment Nova stops being a system that **processes turns** and becomes a system that **maintains a journey**. The architecture is in place; the remaining work is **evidence that the journey feels real to operators**.
