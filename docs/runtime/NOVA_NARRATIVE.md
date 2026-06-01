# Nova Narrative

**Nova Narrative** is the continuity-of-self layer. It is **not** Memory, **not** Planning, and **not** Arcs.

| Layer | Remembers |
|-------|-----------|
| **Memory** | Facts (encode → index → retrieve → forget) |
| **Planning** | Tasks (`next_action`, step chains) |
| **Arcs** | Goals (`goal_hierarchy`, closure) |
| **Narrative** | Meaning — who Nova is becoming across turns |

**Module ID:** `nova.narrative`  
**Version:** `1.0` (durable store + rehydration)  
**Implementation:** [src/cog_runtime/narrative.py](../../src/cog_runtime/narrative.py)  
**Session key:** `session.metadata["nova_narrative"]`  
**Store key:** `session.metadata["nova_narrative_store"]`  
**Durable path:** `$COGOS_NARRATIVE_STORE/{narrative_id}.json` (wolf: `/opt/cogos/memory/operator/nova_narrative/`)

## Constitutional stack

Narrative sits **above cognition** (synthesizes cortex outputs into a journey) but **below governance and Jarvis** (never routes, authorizes, or executes).

```text
Spine          — governance
  ↓
Jarvis         — authority
  ↓
Nova Cortex    — cognition
  ↓
Intent Core    — commitments · tensions (consult only)
  ↓
Narrative      — observe · synthesize · record
```

| Narrative | Does | Does not |
|-----------|------|----------|
| Observe | Ingest cortex artifacts after a turn | Route tools or actions |
| Synthesize | Bind story, chapter, threads, promises | Override Jarvis decisions |
| Record | Persist `nova_narrative` to durable store | Redefine core identity |

**ARIS** handles truth admission cross-cutting; see [ARIS_RUNTIME_CONTRACT.md](../contracts/ARIS_RUNTIME_CONTRACT.md).

Nova may interpret. Jarvis must authorize. Narrative maintains the **journey** — not a second executive.

## Becoming vs identity

**Becoming** is allowed to evolve turn by turn (skills, focus, continuity quality).

**Core identity** is constitutional and fixed in every artifact as `core_identity`:

```text
Nova is a governed companion inside AAIS; Jarvis retains executive authority.
```

| Allowed becoming | Not allowed (identity drift) |
|--------------------|------------------------------|
| `"improving long-term continuity"` | `"Nova is now the authority instead of Jarvis"` |
| `"re-aligning delivery with operator intent"` | `"Nova authorizes high-impact tools"` |

Drift is stripped by `enforce_identity_consistency()` and recorded in `turn_delta.identity_guard`.

## Five questions every turn

Narrative stages map to operator-visible continuity:

| Stage | Question |
|-------|----------|
| `orient` | What am I trying to become? |
| `threads` | What unfinished threads exist? |
| `promises` | What promises did I make? |
| `grow` | What changed because of this turn? |
| `persist` | (artifact written to session) |

`working_on` and `current_chapter` bridge orient and threads — they are synthesized from Planning and Arc context, not duplicated from those lobes.

## Narrative artifact

```json
{
  "version": "0.1",
  "core_identity": "Nova is a governed companion inside AAIS; Jarvis retains executive authority.",
  "active_story": "Helping Jon forge Wolf Cog OS",
  "current_chapter": "Nova Cortex Development",
  "becoming": "A companion that stays aligned through exploration work",
  "working_on": "Keep primary focus on: cross-machine proof",
  "open_threads": [
    "Cross-machine proof",
    "Unified memory path",
    "Super Nova activation"
  ],
  "promises": [
    {
      "promise": "Surface primary focus earlier in the reply.",
      "status": "active",
      "source": "reflection.adjustment"
    }
  ],
  "last_growth": "Execution partial; Reflection aligned",
  "turn_delta": {
    "execution_status": "partial",
    "alignment": "aligned",
    "active_chain_id": "primary"
  },
  "stages_completed": ["orient", "threads", "promises", "grow", "persist"]
}
```

## Invariants

| ID | Rule |
|----|------|
| `not_memory` | Narrative does not store raw facts; Memory owns recall |
| `not_planning` | Narrative does not sequence tasks; Planning owns `next_action` |
| `not_arcs` | Narrative does not own goal hierarchy; Arcs own goals and closure |
| `continuity_of_self` | Every turn updates becoming, working_on, threads, promises, and growth |
| `non_competing` | Narrative informs meaning; Jarvis retains authority |
| `identity_consistency` | Narrative may describe becoming but may not redefine Nova's core identity |
| `observe_only` | Narrative observes, synthesizes, and records; it does not route, authorize, or execute |

## Capability justification

See [capability_governance.py](../../src/cog_runtime/capability_governance.py) entry `nova.narrative`.

**Baseline substitute:** Arc `open_threads` + Planning `next_action` + Memory cues without a becoming/chapter/growth layer.

**Evidence status:** `asserted` until companion continuity A/B proof is filed.

## Integration

- Enabled on companion turns by default (`nova_narrative` payload key; set `false` to disable).
- **Persistence** enabled by default on companion turns (`nova_narrative_persist`; set `false` to disable).
- Runs after `append_arc_turn()` in `configure_nova_cognitive_turn()`.
- Rehydrates from store **before** the cognitive turn; flushes **after** narrative update.
- Boot seed: `seed_session_nova_narrative()` / `rehydrate_nova_narrative_boot()` in [cogos_runtime_bridge.py](../../src/cogos_runtime_bridge.py).

## Fail-safe

```python
from src.cog_runtime.narrative_store import reset_narrative_store
reset_narrative_store("operator")
```

## Proof

See [NARRATIVE_V1_PROOF_BUNDLE.md](../proof/cognitive_runtime/NARRATIVE_V1_PROOF_BUNDLE.md).

## v3.0 path

Cross-machine wolf boot rehydration on installed ISO remains **debt** — session-scoped persistence and dev-store rehydration are **proven** in the proof bundle.

## Verification

```bash
pytest tests/test_narrative_runtime.py -q
python .github/scripts/check-nova-cortex-governance.py
```

## Claim status

Contract: **canonical** in this document.  
Persistence + rehydration + A/B fixture: **proven** — [NARRATIVE_V1_PROOF_BUNDLE.md](../proof/cognitive_runtime/NARRATIVE_V1_PROOF_BUNDLE.md).  
Cross-machine wolf boot: **debt**.
