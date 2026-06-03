# Route Choice V1 Proof

## Claims

| Claim | Label |
|-------|-------|
| Route choice organ reports advisory-only posture | asserted |
| Provider route organ denies execution authority | asserted |

## Reproduction

```bash
make route-choice-organ-gate provider-route-organ-gate specialist-route-organ-gate
python -m pytest tests/test_route_choice_organ.py tests/test_provider_route_organ.py tests/test_specialist_route_organ.py -q
```
