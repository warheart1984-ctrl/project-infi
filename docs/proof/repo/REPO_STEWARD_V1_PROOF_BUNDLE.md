# Repo Steward v1 Proof Bundle

| Field | Value |
|-------|-------|
| **Claim posture** | `asserted` |
| **Authority** | [REPO_PROOF_LAW.md](../../REPO_PROOF_LAW.md) · [RULE_SET.md](../../subsystems/repo_steward/RULE_SET.md) |

## 1) Incident / Issue ID

- ID: RS-MVP-1
- Title: Repo Steward subsystem MVP — workspace hygiene gate
- Scope: Root pollution, mirror trees, bundle staging, stray argv files, local work dirs
- Severity: medium (workspace integrity)
- Linked tracker/docs: [BASELINE_CHECKLIST.md](../../subsystems/repo_steward/BASELINE_CHECKLIST.md) RS-D1

## 2) Hypothesis And Root Cause

- Initial hypothesis: Repo clutter grows because audits exist but nothing enforces them in CI.
- Confirmed root cause: No manifest-driven gate; duplicate trees and accidental bundle paths land at repo root without automated detection.
- Why credible: Prior `git status` noise (~186 items), whitespace poison dir, duplicate import trees on disk.
- Conditions required to trigger: Operator stages Synthetic Mind bundle to wrong cwd, or keeps mirror trees locally.

## 3) Reproduction Steps

- Environment profile(s): Windows dev workstation; Ubuntu CI (clean checkout)
- Preconditions: Manifest and scanner present under `docs/audit/` and `.github/scripts/`
- Steps:
  1. Create `AAIS-main/` at repo root
  2. Run `make repo-hygiene-gate REPO_HYGIENE_MODE=fail`
- Expected failure signal: `hygiene.forbidden_root_name`, exit code 1
- Actual failure signal: matches expected in unit tests

## 4) Fix Details (What / Why / How)

- What changed: Repo Steward subsystem — rule set, schema-validated manifest, manifest-driven scanner, CI workflow, proof bundle
- Why this approach: Stage 2 inspection only (MA-13); no auto-delete; aligns with existing gate patterns
- How it addresses root cause: Machine-enforces ROOT_STRUCTURE_AUDIT buckets on every gate run
- Files/artifacts changed: see [README.md](../../subsystems/repo_steward/README.md)
- Risks and mitigations: Windows file locks on poison dirs — `scripts/repo/remove-poison-dir.py`; CI skips bundle compare on ubuntu

## 5) Verification Evidence

### Commands

```text
python3 .github/scripts/validate-repo-hygiene-manifest.py --mode fail
python3 -m unittest tests.test_check_repo_hygiene_script -q
make repo-hygiene-gate REPO_HYGIENE_MODE=fail
python3 .github/scripts/validate-governance-ledger.py --mode warn --summary-only
```

### Outputs

```text
Repo hygiene manifest: errors=0, mode=fail
Ran 9 tests ... OK
Repo hygiene check: errors=0, warnings=N, mode=fail
Governance ledger check: ... errors=0
```

### Artifact Hashes

- Report path: `ci-artifacts/repo-hygiene-report.json` (uploaded by CI workflow)

### Screenshot / Video References

- CI run URL: pending (debt RS-D1)

## 6) Hardware Matrix

| Machine | Role | Test Set | Outcome | Evidence Ref |
|---------|------|----------|---------|--------------|
| dev-workstation | local | unit tests + make gate | asserted | this bundle |
| github-ubuntu-latest | CI | repo-hygiene-gate.yml | pending URL | RS-D1 |

## 7) Time / Author / Sign-Off

- Start time (UTC): 2026-06-02
- End time (UTC): 2026-06-02
- Author: Stage 2 copilot integration
- Reviewer: pending operator / Meta Architect
- Sign-off: **pending** — promote to `proven` when CI URL recorded

## MA-13

Repo Steward inspects workspace shape only; it does not delete files or mutate repo content.

## Operator remediation

```bash
python scripts/repo/remove-poison-dir.py
make repo-hygiene-gate REPO_HYGIENE_MODE=warn
```
