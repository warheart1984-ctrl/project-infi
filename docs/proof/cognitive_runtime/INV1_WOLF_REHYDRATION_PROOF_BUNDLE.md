# INV-1 Wolf Rehydration Proof Bundle

**Claim:** Narrative + Intent durable stores survive Wolf metal reboot on disk paths under `/opt/cogos/memory/operator/`.

| Field | Value |
|-------|-------|
| **Bundle ID** | `cognitive_runtime.inv1_wolf_rehydration.v1` |
| **Debt register** | INV-1 |
| **Claim posture** | `asserted` (single-machine harness) · cross-machine = `debt` until manifest active |

## Evidence lanes

| Lane | Command | Status |
|------|---------|--------|
| Harness round-trip | `pytest tests/test_wolf_rehydration_harness.py -q` | asserted |
| Bridge CLI | `python -m src.cogos_runtime_bridge --verify-rehydration <store_root>` | asserted |
| Cross-machine replay | `docs/proof/cognitive_runtime/cross_machine/REPLAY_MANIFEST.json` | debt |

## Pre-reboot snapshot (template)

Record before reboot on metal:

- `active_story` from narrative store
- `active_commitments[].commitment_id` from intent store
- SHA-256 of store JSON files

## Post-reboot verification

```bash
python3 -m src.cogos_runtime_bridge --rehydrate-boot operator \
  --narrative-store /opt/cogos/memory/operator/nova_narrative \
  --intent-store /opt/cogos/memory/operator/nova_intent
```

**Pass:** both stores `rehydrated: true`; story + commitments match pre-reboot snapshot.

## Related

- [`cross_machine/README.md`](cross_machine/README.md)
- [`NARRATIVE_V1_PROOF_BUNDLE.md`](NARRATIVE_V1_PROOF_BUNDLE.md)
- [`INTENT_AGENCY_V1_PROOF_BUNDLE.md`](INTENT_AGENCY_V1_PROOF_BUNDLE.md)
