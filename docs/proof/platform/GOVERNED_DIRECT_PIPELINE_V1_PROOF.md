# Governed Direct Pipeline — V1 Proof

CISIV stage: **verification**

## Claims

| Claim | Label |
|-------|-------|
| Inspect API returns schema-valid turn trace | `proven` |
| Lanes separated on fixture turns | `proven` |
| Immune hook present on governed build | `proven` |

## Verification

```bash
make governed-pipeline-gate
python -m pytest tests/test_governed_direct_pipeline.py -q
```
