# Nova Face Organ V1 Proof

## Claims

| Claim | Label |
|-------|-------|
| Status API returns bounded snapshot | asserted |
| Organ surface is read-only | asserted |

## Reproduction

```bash
make nova-face-organ-gate
python -m pytest tests/test_nova_face_organ.py -q
```
