# Repo Steward Subsystem

Governed workspace hygiene gate for the canonical repo root.

## Intent

Repo Steward stops workspace drift before it becomes git noise, mirror ambiguity, or accidental bundle staging. It enforces the inventory in [ROOT_STRUCTURE_AUDIT.md](../../audit/ROOT_STRUCTURE_AUDIT.md) without auto-deleting operator files.

## Active Docs In This Folder

- [RULE_SET.md](./RULE_SET.md) — authoritative rule catalog
- [BASELINE_CHECKLIST.md](./BASELINE_CHECKLIST.md) — MVP baseline and debt register

## Machine surfaces

| Surface | Path |
|---------|------|
| Manifest | [REPO_HYGIENE_MANIFEST.json](../../audit/REPO_HYGIENE_MANIFEST.json) |
| Schema | [repo_hygiene_manifest.v1.json](../../../schemas/repo_hygiene_manifest.v1.json) |
| Manifest validator | [.github/scripts/validate-repo-hygiene-manifest.py](../../../.github/scripts/validate-repo-hygiene-manifest.py) |
| Scanner | [.github/scripts/check-repo-hygiene.py](../../../.github/scripts/check-repo-hygiene.py) |
| CI workflow | [.github/workflows/repo-hygiene-gate.yml](../../../.github/workflows/repo-hygiene-gate.yml) |
| Poison-dir helper | [scripts/repo/remove-poison-dir.py](../../../scripts/repo/remove-poison-dir.py) |

## Operator commands

```bash
make repo-hygiene-gate
python scripts/repo/remove-poison-dir.py
```

## Proof

- [REPO_STEWARD_V1_PROOF_BUNDLE.md](../../proof/repo/REPO_STEWARD_V1_PROOF_BUNDLE.md)

## Rule

Subordinate to `META_ARCHITECT_LAWBOOK.md` and `REPO_PROOF_LAW.md`. No proof, no claim.
