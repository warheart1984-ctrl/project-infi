# Prompt Assembly Organ V1 Proof

## Claims

| Claim | Label |
|-------|-------|
| Status API returns bounded snapshot | asserted |
| Organ surface is read-only | asserted |

## Reproduction

```bash
make prompt-assembly-organ-organ-gate
python -m pytest tests/test_prompt_assembly_organ.py -q
```
