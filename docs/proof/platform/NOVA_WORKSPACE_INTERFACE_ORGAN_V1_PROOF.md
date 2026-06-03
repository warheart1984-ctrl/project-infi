# Nova Workspace Interface Organ V1 Proof

## Claims

| Claim | Label |
|-------|-------|
| Status API returns bounded snapshot | asserted |
| Subsystem surface is read-only | asserted |

## Reproduction

```bash
make nova-workspace-interface-organ-organ-gate
python -m pytest tests/test_nova_workspace_interface_organ.py -q
```
