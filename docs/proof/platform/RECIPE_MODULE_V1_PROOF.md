# Recipe Module v1 Proof Packet

Claim: Governed recipe packs validate, enforce human signoff gates, create Mission Board missions via a distinct API from built-in presets, register on the capability bridge, and emit UL lineage.

Claim status: **proven** on fixture `onboarding-v1` and API/bridge tests.

## Verification

```bash
make recipe-module-gate
python -m pytest tests/test_recipe_module.py tests/test_capability_bridge_alt3.py tests/test_alt3_lineage.py -q
```

| Claim | Label |
|---|---|
| Fixture pack validates; signoff gate enforced | proven |
| Mission created from recipe with signoff | proven |
| Preset endpoint remains separate surface | proven |
| Capability bridge `recipe_module` / `create_mission` | proven |
| UL lineage on create_from_recipe | proven |

- claim_label: proven
- override_command: make recipe-module-gate
