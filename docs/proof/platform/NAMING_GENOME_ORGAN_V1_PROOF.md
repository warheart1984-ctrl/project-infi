# Naming Genome Organ V1 Proof

## Claims

| Claim | Label |
|-------|-------|
| Status API returns bounded snapshot | asserted |
| Subsystem surface is read-only | asserted |

## Reproduction

```bash
make naming-genome-organ-organ-gate
python -m pytest tests/test_naming_genome_organ.py -q
```
