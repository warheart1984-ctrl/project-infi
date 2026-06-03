# Speakers Lane Organ V1 Proof

## Claims

| Claim | Label |
|-------|-------|
| Status API returns bounded snapshot | asserted |
| Organ surface is read-only | asserted |

## Reproduction

```bash
make speakers-lane-organ-gate
python -m pytest tests/test_speakers_lane_organ.py -q
```
