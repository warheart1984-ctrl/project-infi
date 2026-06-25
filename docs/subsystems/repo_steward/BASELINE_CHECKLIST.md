# Repo Steward Baseline Checklist

| Field | Value |
|-------|-------|
| **Subsystem** | Repo Steward MVP |
| **Claim posture** | `asserted` |

## MVP baseline

- [x] Rule set documented ([RULE_SET.md](./RULE_SET.md))
- [x] Machine-readable manifest with `rules[]` ([REPO_HYGIENE_MANIFEST.json](../../audit/REPO_HYGIENE_MANIFEST.json))
- [x] JSON schema ([repo_hygiene_manifest.v1.json](../../../schemas/repo_hygiene_manifest.v1.json))
- [x] Manifest validator (`.github/scripts/validate-repo-hygiene-manifest.py`)
- [x] Enforcement scanner (`.github/scripts/check-repo-hygiene.py`)
- [x] Unit tests (`tests/test_check_repo_hygiene_script.py`)
- [x] CI workflow (`.github/workflows/repo-hygiene-gate.yml`)
- [x] Make target (`make repo-hygiene-gate`)
- [x] Proof bundle scaffold ([REPO_STEWARD_V1_PROOF_BUNDLE.md](../../proof/repo/REPO_STEWARD_V1_PROOF_BUNDLE.md))

## Debt register

| ID | Item | Owner | Severity | Due | Status |
|----|------|-------|----------|-----|--------|
| RS-D1 | First green CI run URL recorded in proof bundle | ops | medium | TBD | open |
| RS-D2 | Promote `hygiene.stale_payload_runtime` to error after payload gitignore stable | eng | low | TBD | open |
