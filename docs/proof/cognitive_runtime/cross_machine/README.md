# Cognitive Runtime — Cross-Machine Replay (INV-1)

Cross-machine proof lane for **Wolf metal reboot narrative + intent rehydration**.

| Field | Value |
|-------|-------|
| **Lane ID** | `cognitive_runtime.cross_machine.v1` |
| **Debt register** | INV-1 |
| **Claim posture** | `asserted` until second-machine evidence filed |

## Activation

1. Set `COGOS_CROSS_MACHINE_REPLAY_ACTIVE=1` on the secondary machine.
2. Copy `REPLAY_MANIFEST.template.json` → `REPLAY_MANIFEST.json` and fill machine IDs.
3. Run pre-reboot companion turn on Wolf metal; flush stores under:
   - `/opt/cogos/memory/operator/nova_narrative/operator.json`
   - `/opt/cogos/memory/operator/nova_intent/operator.intent.json`
4. Reboot installed disk.
5. Post-reboot: run bridge CLI or harness commands below.
6. Attach hashes to proof bundle [`INV1_WOLF_REHYDRATION_PROOF_BUNDLE.md`](../INV1_WOLF_REHYDRATION_PROOF_BUNDLE.md).

## Repo-side smoke (single machine, asserted)

```bash
python -m src.cogos_runtime_bridge --verify-rehydration /tmp/wolf-rehydration-test
bash scripts/cogos/verify-wolf-rehydration.sh
pytest tests/test_wolf_rehydration_harness.py -q
```

## Metal commands (post-reboot)

```bash
export COGOS_RUNTIME=wolf
python3 /opt/cogos/runtime/src/cogos_runtime_bridge.py --rehydrate-boot operator \
  --narrative-store /opt/cogos/memory/operator/nova_narrative \
  --intent-store /opt/cogos/memory/operator/nova_intent
```

**Pass criteria:** `rehydrated: true` for both narrative and intent; `active_story` and `active_commitments` match pre-reboot snapshot hashes.

See also: [`cog-os/docs/METAL_PROOF_CHECKLIST.md`](../../../cog-os/docs/METAL_PROOF_CHECKLIST.md) — Nova store rehydration and metal boot proof.
