# Culture Habit V1 Proof

Status: **Release 36 / Anatomical Stage 5**

## Scope

Governed habit formation over time: HCC-0 mining, HCC-2 operator adoption into preference slot, mesh-aware habit boost for organ planning.

## Contract

- [CULTURE_HABIT_CONTRACT.md](../../contracts/CULTURE_HABIT_CONTRACT.md)
- Schemas: `operator_habit.v1`, `habit_pattern.v1`

## Modules

| Module | Role |
|--------|------|
| `src/culture_habit_runtime.py` | Pattern mining, ranking, adoption |
| `src/culture_habit_registry.py` | Adopted habit registry |
| `src/jarvis_habit_authority.py` | Jarvis gate for habit-influenced routing |
| `src/habit_adoption_bridge.py` | Brain accept → adoption approval enqueue |

## APIs

| Route | Behavior |
|-------|----------|
| `GET /api/operator/culture` | Culture snapshot |
| `POST /api/operator/culture/observe` | HCC-0 mine |
| `GET /api/operator/culture/habits` | Adopted + candidates |
| `POST /api/operator/culture/habits/adopt` | HCC-2 promote (403 without operator_approved) |

## Verification

```bash
make culture-habit-gate
python -m pytest tests/test_culture_habit_observe.py tests/test_culture_habit_adopt.py -q
```

## Success criteria

- Recurring ledger/mesh sequences surface as HCC-0 candidates
- Operator promote writes registry + preference overlay; ledger receipt emitted
- Brain accept enqueues habit adoption approval; does not auto-adopt
- Adopted mesh habit boosts matching handoff edge in mesh planner
- Somatic panel shows adopted_habits / habit_candidates
