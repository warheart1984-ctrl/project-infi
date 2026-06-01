# Nova Coherence Projection

**Coherence Projection** is not a lobe. It is the integration layer that makes the **voice speak from the mind** instead of beside it.

## Problem

Nova Cortex produces artifacts (`intent`, `narrative`, `decision`, `arc`, `planning`) **before** `generate_chat`. Until projection, those artifacts lived on `session.metadata` but did not systematically reach the LLM.

```text
Mind  ──disconnected──▶  Voice        (before)
Mind  ──projection────▶  Voice        (after)
```

## Stack position

```text
Jarvis (authority)
  ↓
Nova Cortex (cognition — lobes + Intent + Narrative)
  ↓
Coherence Projection (read-only state export)
  ↓
Provider LLM (local or cloud)
  ↓
Speaking Runtime (presentation)
  ↓
Output
```

| Layer | Role |
|-------|------|
| **Cortex** | Produces artifacts + ledger |
| **Projection** | Exports bounded state — not chain-of-thought |
| **LLM** | Generates language **from** that state |
| **Speaking** | Formats user-visible reply |

## Projection payload

Built by `build_coherence_projection()` in [coherence_projection.py](../../src/cog_runtime/coherence_projection.py):

```json
{
  "projection_version": "1.0",
  "read_only": true,
  "intent": {
    "agency_note": "...",
    "active_tensions": [{"poles": "safety ↔ exploration", "pull": "safety"}],
    "active_commitments": [{"commitment": "...", "status": "active", "claim_posture": "asserted"}],
    "continuity_claim_posture": "asserted",
    "long_horizon_goal": "..."
  },
  "narrative": {
    "active_story": "...",
    "becoming": "...",
    "working_on": "...",
    "current_chapter": "..."
  },
  "cognition": {
    "primary_focus": "...",
    "decision": {"chosen_option": "...", "rationale": "..."},
    "next_action": "...",
    "arc": {"root_goal": "...", "goal_type": "continuity", "turn_count": 2}
  }
}
```

Injected as modular context channel `cognitive` via `NovaCoherenceProjectionModule` in [jarvis_modular.py](../../src/jarvis_modular.py).

## Invariants

- **Read-only** — projection does not route, authorize, or mutate cortex state
- **No raw chain-of-thought** — bounded fields only; instruction tells model not to expose modules
- **Jarvis authority** — executive control unchanged
- **Absent when cortex off** — no projection block if `cognitive_runtime_enabled` is false

## Wiring

1. `configure_nova_cognitive_turn()` runs **before** chat generation (`api.py`)
2. `build_chat_turn_modular_preview()` copies `nova_intent`, `nova_narrative`, `cortex_arc`, artifacts into turn metadata
3. `NovaCoherenceProjectionModule.collect()` adds one system module before `generate_chat`

## Verification

```bash
pytest tests/test_coherence_projection.py -q
```

**Claim status:** modular injection + projection schema = **asserted** (single-machine pytest).

Cross-machine proof that operator replies reflect projected state under session reset = **debt**.
