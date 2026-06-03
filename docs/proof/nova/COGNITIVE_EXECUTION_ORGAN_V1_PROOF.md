# Cognitive Execution Organ V1 Proof

## Claims

| Claim | Label |
|-------|-------|
| Status API returns bounded snapshot | asserted |
| Organ surface is read-only | asserted |

## Reproduction

```bash
make cognitive-execution-organ-gate
python -m pytest tests/test_cognitive_execution_organ.py -q
```
