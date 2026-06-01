# Forge Profile Precedence Policy (P0 Draft)

Status: approved contract draft for P0 plumbing

## Resolution Order

1. Explicit CLI `--profile` selection (highest precedence)
2. `COGOS_FORGE_PROFILE` environment variable
3. `COGOS_BOOT_PROFILE` environment variable when value starts with `forge`
4. Default profile id: `forge-selfhosted`

## Policy Rules

- Profile files define defaults and should be deterministic.
- Environment/CLI selection controls only which profile file is selected.
- Environment values must not mutate profile file contents.
- If multiple selectors are present, the highest precedence source wins.
- Unknown profile ids fail validation in `fail` mode and warn in `warn` mode.

## Evidence Contract

- CI dry-run must emit:
  - `ci-artifacts/profile-validation.json`
  - `ci-artifacts/profile-attestation.json`
- Emitted evidence must include:
  - selected profile id
  - precedence source (`cli`, `env.COGOS_FORGE_PROFILE`, `env.COGOS_BOOT_PROFILE`, `default`)
  - resolved profile file path
