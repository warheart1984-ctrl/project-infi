# Cross-Machine Proof Folder

## State: Inactive

This folder holds second-machine replay evidence **after** activation.
Until then, only the template manifest and README exist.

Do not mark cross-machine claims `proven` from this folder while inactive.

## Activation Checklist

1. Copy `REPLAY_MANIFEST.template.json` to `REPLAY_MANIFEST.json`
2. Fill machine identity, Python version, and expected command list
3. Set `FORGE_CROSS_MACHINE_REPLAY_ACTIVE=1` for the replay session only
4. Run `scripts/forgekeeper/cross-machine-replay.ps1` or `.sh`
5. Append transcripts and hashes to `STAGE1_PROOF_BUNDLE.md` hardware matrix
6. Unset activation env when done

## Expected Outputs (post-activation)

- `replay_transcript.txt` — command log (optional, operator-created)
- `replay_hashes.json` — captured artifact hashes from second machine

These files are optional until activation; do not commit secrets or host PII.
