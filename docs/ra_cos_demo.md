# RA-COS 10-Minute Demo

## Story (one sentence)

When reality diverges from our thresholds, the system detects it, governs the change through adversarial review, updates the threshold registry, and leaves an audit trail — without silent drift.

## Proof commands

```bash
cd project-infi
pytest tests/test_ra_cos_loop.py -v
python -m src.continuity.demo.ra_cos_demo --db data/demo_ra_cos.sqlite3
```

Or after install:

```bash
ra-cos-demo --db data/demo_ra_cos.sqlite3 --lineage-out demo_lineage.md
```

## Demo script (10 minutes)

| Minute | Beat | What to show |
|--------|------|----------------|
| 0–2 | Setup | Seeded `propagation_count` (value **3**) and safety threshold (value **0**) |
| 2–4 | Trigger | Event + `validation={"late_intervention": true}` → triggers fire |
| 4–6 | Governance | Five-Team review → **approved** ledger event with legitimacy basis |
| 6–8 | Registry | Threshold **3 → 2** in SQLite; `threshold_versions` grows |
| 8–9 | Rejection | Safety 0→1 attempt → **CRK INV_001** reject; registry unchanged; ledger has rejection |
| 9–10 | Lineage | Markdown report + chart spec — every change attributable |

### Audience flags

```bash
python -m src.continuity.demo.ra_cos_demo --audience investor
python -m src.continuity.demo.ra_cos_demo --audience technical
python -m src.continuity.demo.ra_cos_demo --audience governance
python -m src.continuity.demo.ra_cos_demo --audience all   # default
```

## Persistence surface

SQLite file: `data/ra_cos.sqlite3` (override with `RACOS_STORE_PATH`).

| Table | Purpose |
|-------|---------|
| `thresholds` | Current threshold snapshots |
| `threshold_versions` | Append-only version history |
| `recalibration_events` | Append-only governance ledger |
| `observation_patterns` | Stub for interpretive stewardship (no writes this quarter) |

Schema: [`fixtures/continuity/ra_cos_threshold.sql`](../fixtures/continuity/ra_cos_threshold.sql)

## Core code path

1. [`detect_recalibration_triggers`](../src/continuity/ra/recalibration_triggers.py)
2. [`process_ra_cos_event`](../src/continuity/ra/ra_cos_loop.py)
3. [`RacosThresholdStore`](../src/continuity/css2/threshold_store.py)
4. [`RACOS1Layer.process_recalibration_event`](../src/stack/ra_cos1_api.py)

## Credibility line (outsiders)

In three months I built a governed continuity substrate: explicit thresholds, recalibration triggers, constitutional invariants, Five-Team adversarial review, and an append-only recalibration ledger. The repo is large because it encodes a full governance laboratory; the product slice is the RA-COS loop from trigger to ledger to registry update.

## Parked for this quarter (out of demo scope)

- TypeScript loop as primary runtime (`continuity-engine/src/ra-cos1/event-loop.ts` — reference only)
- 199 organ smokes / broad test expansion
- `docs/_future/`, mesh/federation, USL, most of `archive/`
- Operator dashboard (`src/dashboard/`)
- Postgres / full ORM
- New subsystem genomes or constitutional articles
- `observation_patterns` writes (table stub only)
