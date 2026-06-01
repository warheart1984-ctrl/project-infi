# AI Mechanic STAGE0 Proof Bundle

| Field | Value |
|-------|-------|
| **Subsystem** | AI Mechanic MVP |
| **Claim** | `asserted` (single-machine pytest + governance gate) |
| **Date** | 2026-05-31 |

## What is proven (asserted)

- Generic repo scan produces `process_genome.v1`
- Diagnosis emits GOV/RNT/CST/HUM codes on fixture repo
- Rebuild emits four dry-run artifacts without mutating fixture repo
- `apply` mode blocked
- Runtime enforcer rejects over-budget / missing audit fields

## Verification

```bash
pytest tests/test_mechanic.py -q
python .github/scripts/check-mechanic-governance.py
make mechanic-gate
```

## Fixture

`mechanic/fixtures/sample-customer-repo/`

## Debt

- MECH-LLM-01, MECH-TRIBAL-01, MECH-TRACE-01, MECH-APPLY-01, MECH-CHAT-01, MECH-XM-01
