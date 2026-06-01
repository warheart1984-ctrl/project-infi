# AI Factory

**Governed mind fabrication pipeline** — not a model zoo, fine-tune farm, or agent playground.

| Field | Value |
|-------|-------|
| **Factory ID** | `ai_factory.v1` |
| **Version** | 1.0 |
| **Authority** | Meta Architect Lawbook · Stage 2 Copilot Doctrine (MA-13) |
| **Claim posture (v1)** | `asserted` — single-machine pytest + hash manifest |

## What this is

The AI Factory repeatedly builds **governed minds from spec**:

- Constitutional spine bound per build
- Composed cognitive runtime (Nova Cortex + Spark v1 default)
- Proof bundle and verification lanes
- Deployment envelope with build receipt and hash manifest

Every build emits: **spec → spine profile → runtime bundle → proof → receipt → ledger entry**.

## What this is not

- Model training or weight production
- Unbounded agent playground
- CI/CD without constitutional gates

## Stations (v1)

| Station | Input | Output |
|---------|-------|--------|
| Spec | YAML/JSON order form | `AI_BUILD_SPEC.json` |
| Spine | Build spec | `SpineProfile.json` |
| Runtime | Spec + spine | `CORTEX_RUNTIME_BUNDLE.json` |
| Binding (stub) | Spec | `BOUND_CAPABILITY_PROFILE.json` |
| Proof | Assembled unit | `AI_PROOF_BUNDLE.md`, `proof_manifest.json` |
| Envelope | Verified build | `AI_BUILD_RECEIPT.json`, station receipts |
| Lifecycle (minimal) | Live telemetry | ledger lookup, revoke receipt |

## Operator commands

```bash
python -m ai_factory build --spec factory/specs/nova-default.yaml
make ai-factory-build SPEC=factory/specs/nova-default.yaml
make ai-factory-gate
python -m ai_factory status --build-id nova-default
python -m ai_factory deploy --build-id nova-default
python -m ai_factory revoke --build-id nova-default
```

Build artifacts land under `.runtime/ai_factory/<build_id>/`.

## Schemas

- `ai_factory/schemas/ai_build_spec.v1.json`
- Receipt: `ai_factory.build_receipt.v1`
- Spine profile: `ai_factory.spine_profile.v1`
- Runtime bundle: `ai_factory.cortex_bundle.v1`
- Proof manifest: `ai_factory.proof_manifest.v1`

Reference spec: [`factory/specs/nova-default.yaml`](../../factory/specs/nova-default.yaml)

## Doctrine boundaries (MA-13)

| Failure class | Factory guard |
|---------------|---------------|
| Class I — Usurpation | Spec cannot silently invent Stage 1 goals; Jarvis remains executive in runtime bundle |
| Class II — Distortion | Prohibitions and oversight fields are canonical; spine profile must not widen permissions |
| Class III — Leakage | Proof station blocks deploy on constitutional failure when `risk_level: high` |

## v1 exclusions

- Live `api.py` spine profile wiring (proof adapter only)
- Cross-machine replay (status: inactive)

## v1.1 (asserted single-machine)

- Wolf CoG OS payload deploy: `python -m ai_factory deploy --build-id <id> --wolf`
- Promotes `CORTEX_RUNTIME_BUNDLE` → `wolf-cog-os/payload/opt/cogos/config/cognitive_runtime_family.json`
- Artifacts under `wolf-cog-os/payload/opt/cogos/runtime/factory/`
- Model zoo / dynamic tool binding engine

## Proof

See [`docs/proof/ai_factory/AI_FACTORY_V1_PROOF_BUNDLE.md`](../proof/ai_factory/AI_FACTORY_V1_PROOF_BUNDLE.md).

## Related docs

- [NOVA_CORTEX.md](./NOVA_CORTEX.md)
- [STAGE2_COPILOT_DOCTRINE.md](./STAGE2_COPILOT_DOCTRINE.md)
- [NOVA_CAPABILITY_INVENTORY.md](./NOVA_CAPABILITY_INVENTORY.md)
