# Nova Intent Core

**Nova Intent Core** holds **agency** and **tension** — not another authority, not another planner.

| Layer | Persists |
|-------|----------|
| **Memory** | Facts (recall) |
| **Planning** | Tasks (`next_action`, chains) |
| **Intent** | Commitments, values, horizon goals, **current tensions**, conflicts, closure posture |
| **Narrative** | Story (meaning; may change daily) |

**Module ID:** `nova.intent`  
**Version:** `0.2`  
**Implementation:** [src/cog_runtime/intent_core.py](../../src/cog_runtime/intent_core.py)  
**Consult helpers:** [src/cog_runtime/intent_consult.py](../../src/cog_runtime/intent_consult.py)  
**Session key:** `session.metadata["nova_intent"]`  
**Store key:** `session.metadata["nova_intent_store"]`  
**Durable path:** `$COGOS_INTENT_STORE/{intent_id}.json` (wolf: `/opt/cogos/memory/operator/nova_intent/`)

## Why Intent exists

Deliberation chooses between options. Narrative describes becoming. Neither necessarily holds **enduring tension** or **commitments that survive story change**.

Humans are pulled between competing forces (safety ↔ exploration, present ↔ future). Much of thinking is **resolution of tension**, not linear input → process → output.

**Agency** (not autonomy): the ability to maintain a goal across interruptions — still committed tomorrow, not merely remembering yesterday.

## Constitutional stack

```text
Spine → Jarvis → Nova Cortex → Intent Core → Narrative
```

| Intent Core | Does | Does not |
|-------------|------|----------|
| Orient | Maintain commitments, tensions, claim posture | Route or authorize |
| Resolve | Surface conflicts (`in_tension`, `deferred`) | Override Deliberation |
| Close | Record `unified_closure` across arc / execution / intent | Replace Planning chains |
| Consult | `intent_context_for_lobes()` consumed by Deliberation + Planning | Override Jarvis |

## v0.2 integration (items 1–5)

| # | Capability | Where |
|---|------------|--------|
| 1 | **Lobe consult** — Deliberation `intent_alignment` criterion; Planning chain scoring | `intent_consult.py`, `deliberation.py`, `planning.py` |
| 2 | **Conflict + deferral** — `commitment_conflicts`, `in_tension_with`, `deferred` | `intent_core.py` |
| 3 | **Unified closure** — `unified_closure.layers` (arc, execution, intent) | `synthesize_unified_closure()` |
| 4 | **Claim posture** — per-commitment `claim_posture`, artifact `continuity_claim_posture` | `intent_core.py`, Narrative `intent_report` |
| 5 | **Evidence fixtures** — session-reset harness + survival metrics | [INTENT_AGENCY_V1_PROOF_BUNDLE.md](../proof/cognitive_runtime/INTENT_AGENCY_V1_PROOF_BUNDLE.md) |

## Intent artifact (v0.2)

```json
{
  "version": "0.2",
  "active_commitments": [
    {
      "commitment": "Finish cross-machine proof",
      "status": "active",
      "source": "operator",
      "claim_posture": "asserted"
    }
  ],
  "long_horizon_goals": [
    {"goal": "Persistent continuity", "claim_posture": "asserted"}
  ],
  "current_tensions": [
    {"poles": ["safety", "exploration"], "pull": "safety", "reason": "..."}
  ],
  "commitment_conflicts": [],
  "unified_closure": {"unified": false, "layers": [], "summary": "No unified closure this turn."},
  "continuity_claim_posture": "asserted",
  "agency_note": "Still committed to 'Persistent continuity' while pulled toward safety (1 active commitment(s))."
}
```

Commitment statuses: `active`, `resolved`, `deferred`, `superseded`, `in_tension`.

## Turn pipeline (Jarvis companion)

1. Rehydrate intent store
2. Inject `intent_*` into cortex context (**prior** intent consulted this turn)
3. Run lobes (Deliberation + Planning weight against intent)
4. `run_intent_turn()` — merge, conflicts, closure, posture
5. `run_narrative_turn()` — `intent_report` + `turn_delta.unified_closure`
6. Flush stores

## Verification

```bash
pytest tests/test_intent_core.py tests/test_intent_store.py tests/test_intent_agency_evidence.py -q
python .github/scripts/check-nova-intent-agency.py
python .github/scripts/check-nova-cortex-governance.py
```

| Claim | Status |
|-------|--------|
| Consult integration + conflicts + closure + session-reset fixture (single-machine) | **proven** — [INTENT_AGENCY_V1_PROOF_BUNDLE.md](../proof/cognitive_runtime/INTENT_AGENCY_V1_PROOF_BUNDLE.md) |
| Wolf metal reboot same commitments | **debt** |
