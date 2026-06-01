# Contributing to Project Infinity / AAIS

Thank you for contributing. This repository is **law-governed**: implementation changes must stay aligned with constitutional precedence and proof requirements.

**Precedence:** Law > Blueprint > Contract > Implementation > Pipeline > Tool

## Before you open a PR

1. Read [`META_ARCHITECT_LAWBOOK.md`](META_ARCHITECT_LAWBOOK.md) and [`REPO_PROOF_LAW.md`](REPO_PROOF_LAW.md).
2. Run the smallest relevant gate for your change (see [`Makefile`](Makefile) targets).
3. Label significant claims as `asserted`, `proven`, or `rejected` in the PR body.
4. Link proof artifacts (pytest output, trust bundle path, or proof doc under `docs/proof/`).

## Local setup

```bash
git clone https://github.com/warheart1984-ctrl/Project-Infinity1.git
cd Project-Infinity1
python -m pip install -e ".[dev]"
cp .env.example .env
python -m aais prepare --data-dir ./.runtime/aais-data
python -m aais start --data-dir ./.runtime/aais-data --preset mock --no-browser
```

Full operator primer: [`README.md`](README.md) — **How to Make It Work**.

## What not to commit

Local-only artifacts are listed in [`.gitignore`](.gitignore). Never commit:

- ISO images (`*.iso`) or forge output under `wolf-cog-os/output/`
- Runtime data under `.runtime/`
- Secrets (`.env`, API keys)
- Duplicate import trees (`AAIS-main/`, `Project-Infinity-main/`, etc.)

## CI on GitHub

Pull requests to `main` run governance workflows under [`.github/workflows/`](.github/workflows/), including:

| Workflow | Purpose |
|---|---|
| `cogos-ci-public.yml` | Core sanity + governance checks |
| `ugr-trust-bundle-gate.yml` | UGR trust bundle organ |
| `ugr-operator-console-gate.yml` | Operator console manifest + tests |
| `documentation-baseline-gate.yml` | Documentation baseline |
| `forgekeeper-governance-gate.yml` | Forgekeeper governance ledger |
| `scorpion-governance-gate.yml` | Scorpion OS anomaly extractor governance |

## Branch policy

- Target **`main`** for integrated work.
- Keep PRs focused; link program docs under `docs/programs/` when touching UGR or Cloud Forge tracks.

## Questions

Open a discussion or issue on GitHub, or follow escalation rules in [`HUMAN_AI_CO_COLLABORATION_CHARTER.md`](HUMAN_AI_CO_COLLABORATION_CHARTER.md).
