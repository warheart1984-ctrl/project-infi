# Nova Narrative v1.0 — Proof Bundle

**Claim:** Nova Narrative persists across session boundaries, rehydrates on boot seed, beats arc+planning-only baseline on continuity questions, and enforces identity consistency.

**Status:** `proven` (single-machine pytest + A/B fixture). Cross-machine wolf boot rehydration: **debt**.

## Scope

| Deliverable | Path |
|-------------|------|
| Narrative v1.0 | [src/cog_runtime/narrative.py](../../src/cog_runtime/narrative.py) |
| Durable store | [src/cog_runtime/narrative_store.py](../../src/cog_runtime/narrative_store.py) |
| Continuity A/B | [src/cog_runtime/narrative_continuity.py](../../src/cog_runtime/narrative_continuity.py) |
| Nova wiring | [src/cog_runtime/nova.py](../../src/cog_runtime/nova.py) |
| Boot rehydration | [src/cogos_runtime_bridge.py](../../src/cogos_runtime_bridge.py) |
| Spec | [docs/runtime/NOVA_NARRATIVE.md](../../docs/runtime/NOVA_NARRATIVE.md) |
| Wolf store dir | [wolf-cog-os/payload/opt/cogos/memory/operator/nova_narrative/](../../wolf-cog-os/payload/opt/cogos/memory/operator/nova_narrative/) |

## Verification

```bash
pytest tests/test_narrative_runtime.py tests/test_narrative_store.py tests/test_narrative_continuity_proof.py -q

python .github/scripts/check-nova-narrative-continuity.py

python -c "from src.cogos_runtime_bridge import rehydrate_nova_narrative_boot; import json; print(json.dumps(rehydrate_nova_narrative_boot('missing-id'), indent=2))"
```

## Claims and evidence

| # | Claim | Label | Evidence |
|---|-------|-------|----------|
| 1 | Persistence survives session end | **proven** | `test_cross_session_rehydration`, `test_configure_companion_turn_persists_to_store` |
| 2 | A/B beats arc+planning baseline on `done` + completeness | **proven** | `test_narrative_continuity_proof.py`, continuity gate fixture |
| 3 | Boot rehydration bridge loads same `active_story` | **proven** | `test_boot_rehydrate_bridge`, `rehydrate_nova_narrative_boot()` |
| 4 | Identity consistency guard enforced | **proven** | `test_identity_drift_is_detected_and_guarded` |
| 5 | Wolf metal boot → same narrative | **debt** | Requires cross-machine ISO proof |

## Continuity questions (treatment artifact)

Every narrative artifact includes `continuity_answers`:

| Question | Field |
|----------|-------|
| What am I doing? | `continuity_answers.doing` ← `working_on` |
| What have I done? | `continuity_answers.done` ← `last_growth` |
| What am I working toward? | `continuity_answers.toward` ← `active_story` + `becoming` + threads |

Baseline substitute (arc + planning only) lacks reliable `done` — narrative treatment wins on fixture.

## Store layout

```text
${COGOS_NARRATIVE_STORE:-.runtime/nova_narrative}/{narrative_id}.json
/opt/cogos/memory/operator/nova_narrative/{narrative_id}.json   # wolf-cog-os-full
```

## Fail-safe

```python
from src.cog_runtime.narrative_store import reset_narrative_store
reset_narrative_store("operator")
```

## Debt

- Cross-machine wolf-cog-os-full boot rehydration on installed ISO
- Operator-rated continuity study (human A/B) beyond automated fixture
