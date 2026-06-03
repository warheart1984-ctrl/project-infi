# Jarvis Console Surface Organ V1 Proof

## Claims

| Claim | Label |
|-------|-------|
| Status API returns bounded snapshot | asserted |
| Organ surface is read-only | asserted |

## Reproduction

```bash
make jarvis-console-surface-organ-organ-gate
python -m pytest tests/test_jarvis_console_surface_organ.py -q
```
