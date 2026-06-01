# Governance Command Ledger

The command governance ledger keeps drift-prone command contracts explicit and machine-checkable.

- Ledger file: `../../.github/governance/command-ledger.json`
- Validator: `../../.github/scripts/validate-governance-ledger.py`
- Local shortcut: `make governance-check`

## What Is Tracked

Each command entry records:

- `id`: stable command identifier (`make.installer-smoke`, `script.github.sanitize-tag`, etc.)
- `owner`: authoritative file/component path
- `invocation`: expected command contract (`make_target` or `script_path`)
- `required_env` / `optional_env`: env var contract for command consumers
- `deprecation`: status and replacement path
- `verification_policy`: `warn` or `fail`
- `consumers`: repository usage references (workflow files and expected snippets)

## How Validation Works

`validate-governance-ledger.py` checks for drift between the ledger and repository state:

1. Validates ledger schema and duplicate command ids.
2. Confirms owner files and invocation paths exist.
3. For `make_target` commands, verifies targets still exist in the specified Makefile.
4. Verifies each consumer file still contains the expected invocation snippet.
5. Flags required env vars when they are not referenced by the listed consumers.
6. Flags deprecated commands that are still in active use.

Default enforcement is `warn` per command to avoid breaking current flows during rollout. Set command policy to `fail` once the contract is stable.

## Local Usage

Run with per-command policy from the ledger:

```bash
python3 ../../.github/scripts/validate-governance-ledger.py
```

Force warn-only mode:

```bash
python3 ../../.github/scripts/validate-governance-ledger.py --mode warn
```

Force fail mode (hard gate):

```bash
python3 ../../.github/scripts/validate-governance-ledger.py --mode fail
```

Make target:

```bash
make governance-check
```

## Updating the Ledger

When a command interface changes:

1. Update the real command implementation first (Make target/script/workflow).
2. Update the matching entry in `../../.github/governance/command-ledger.json`:
   - `invocation` for new target/path
   - env vars (`required_env` / `optional_env`)
   - `consumers` snippet references
3. If retiring a command:
   - set `deprecation.status` to `deprecated`
   - set `deprecation.replacement` to the new command id/path
   - keep `verification_policy: warn` until all consumers migrate
4. Run `make governance-check` and review warnings/errors.
5. After migration is complete, switch policy to `fail` to enforce.
