# Perception Gateway V1 Proof

## Claims

| Claim | Label |
|-------|-------|
| Document and UI vision env gates reported in gateway posture | asserted |
| Perception gateway organ reports bridge-safe flags | asserted |

## Reproduction

```bash
make perception-gateway-organ-gate document-vision-organ-gate ui-vision-organ-gate
python -m pytest tests/test_perception_gateway_organ.py tests/test_document_vision_organ.py tests/test_ui_vision_organ.py -q
```
