# Platform Cross-Machine Replay

Inactive until operator sets `operational_status` to `active` in the replay manifest.

## Template

Copy `REPLAY_MANIFEST.template.json` and fill primary/secondary machine metadata.

## Commands

```bash
python -m platform replay --manifest docs/proof/platform/cross_machine/REPLAY_MANIFEST.template.json
make platform-gate
```

## Claim posture

**`debt`** until CI matrix `.github/workflows/platform-cross-machine-gate.yml` runs on two hosts with matching hashes.
