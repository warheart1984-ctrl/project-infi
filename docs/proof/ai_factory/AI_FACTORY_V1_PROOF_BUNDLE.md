# AI Factory v1 Proof Bundle

**Claim label:** `asserted` (single-machine; cross-machine replay inactive)

## Scope

First end-to-end governed mind build from YAML spec through envelope receipt.

## Build

```bash
make ai-factory-gate
```

Or:

```bash
python -m ai_factory build --spec factory/specs/nova-default.yaml
python -m pytest tests/test_ai_factory.py -q
```

## Expected artifacts

Under `.runtime/ai_factory/nova-default/`:

- `AI_BUILD_SPEC.json`
- `SpineProfile.json`
- `CORTEX_RUNTIME_BUNDLE.json`
- `BOUND_CAPABILITY_PROFILE.json`
- `AI_PROOF_BUNDLE.md`
- `proof_manifest.json`
- `AI_BUILD_RECEIPT.json`
- `station_receipts/*.json`

Ledger: `.runtime/ai_factory/factory_ledger.jsonl`

## Verification lanes

| Lane | Command |
|------|---------|
| constitutional | `pytest tests/test_nova_formal_spec.py tests/test_spark_pipeline.py` |
| composed_turn | `pytest tests/test_aais_composed_runtime.py` |
| capability_governance | `pytest tests/test_capability_governance.py` |
| nova_cortex_gate | `python .github/scripts/check-nova-cortex-governance.py` |
| agency | `pytest tests/test_intent_agency_evidence.py` |
| factory | `pytest tests/test_ai_factory.py` |

## Environment

- Repository: project-infi
- Factory version: `ai_factory.v1`
- Default spec: `factory/specs/nova-default.yaml`

## Template

See [`templates/PROOF_BUNDLE_TEMPLATE.md`](../../templates/PROOF_BUNDLE_TEMPLATE.md).

## Sign-off

- [ ] Operator verified `AI_BUILD_RECEIPT.json` hash manifest
- [ ] Claim remains `asserted` until cross-machine evidence attached
