# AAIS Flagship Cross-Machine Verification

Authority: `REPO_PROOF_LAW.md`, `templates/PROOF_BUNDLE_TEMPLATE.md` §6.

## Purpose

Record independent verification of UL/CISIV and flagship gate commands across at least two machine profiles before upgrading cross-machine claims from **asserted** to **proven**.

## Commands

Primary host (Windows or operator primary):

```bash
python tools/proof/run_flagship_cross_machine_matrix.py --role primary
```

Secondary host (Linux/macOS or clean operator machine):

```bash
python tools/proof/run_flagship_cross_machine_matrix.py --role secondary
```

Copy `.runtime/cross_machine_matrix/secondary-*.json` from the secondary host into the primary workspace, then compare:

```bash
python tools/proof/run_flagship_cross_machine_matrix.py --compare
```

## Artifacts

| Artifact | Location |
|----------|----------|
| Primary profile | `.runtime/cross_machine_matrix/primary-*.json` |
| Secondary profile | `.runtime/cross_machine_matrix/secondary-*.json` |
| Matrix comparison | `.runtime/cross_machine_matrix/matrix_comparison.json` |
| Replay manifest | `docs/proof/aais-ul/cross_machine/REPLAY_MANIFEST.v1.json` |

## Claim posture

- Single-host only: **asserted**
- Primary + secondary parity (all gate commands pass on both hosts): **proven**

See also: `docs/proof/aais-ul/FLAGSHIP_CROSS_MACHINE_MATRIX.md`
