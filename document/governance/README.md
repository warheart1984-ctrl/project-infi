# Governance Checks

Top-level repository law enforcement is validated by two focused checks:

1. **Command-surface drift and contract checks**
   - Script: `../../.github/scripts/validate-governance-ledger.py`
   - Source ledger: `../../.github/governance/command-ledger.json`
   - Purpose: verifies command contracts (owners, invocation targets, consumer presence, env references, deprecation status).

2. **Repo-safety destructive-command checks**
   - Script: `../../.github/scripts/check-repo-safety.py`
   - Purpose: scans command surfaces for prohibited destructive patterns (e.g. `git clean -fdx`, `git reset --hard`, broad `rm -rf` forms).

## Local Verification Commands

```bash
python ../../.github/scripts/validate-governance-ledger.py --mode fail
python ../../.github/scripts/check-repo-safety.py
```

Both commands are designed to fail with explicit, actionable diagnostics when violations are detected.

## Operator Promotion Runbook

- Final promotion checklist and repeatable command bundle:
  - `final-promotion-checklist.md`
