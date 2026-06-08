# Contributing to Project Infinity / AAIS

Thank you for contributing. This repository is **law-governed**: implementation changes must stay aligned with constitutional precedence and proof requirements.

**Precedence:** Law > Blueprint > Contract > Implementation > Pipeline > Tool

**Help Wanted hub:** [`docs/community/HELP_WANTED_HUB.md`](docs/community/HELP_WANTED_HUB.md) · Pinned call: [Stage 18 — Call for Co-Builders](https://github.com/warheart1984-ctrl/Project-Infinity1/discussions/9)

## Contribution tiers

We grow contributors in layers. You do not need permission to start at **Reviewer** — claim a bite-sized issue and open a PR.

| Tier | Typical work | How to level up |
|------|----------------|-----------------|
| **Reviewer** | Triage `help wanted` issues, review PRs, run local gates, improve docs | Merge 1–2 focused PRs with green CI |
| **Subsystem owner** | Own one civilizational or body subsystem, its tests, and proof bundle | Sustained ownership of a subsystem + verification scripts |
| **Core** | Cross-cutting runtime, lawbook, flagship gates, release train | Invitation after track record; charter alignment required |

**Entry path:** README [**How to join in 10 minutes**](README.md#how-to-join-in-10-minutes) → pick an issue from the [co-builder discussion](https://github.com/warheart1984-ctrl/Project-Infinity1/discussions/9) → run the gate listed in the issue body.

**Gates by change type:**

| Change | Minimum local check |
|--------|---------------------|
| Civilizational arc (diplomacy, norms, evolution) | `make civilizational-arc-smoke` or subsystem body gate in issue |
| Operator / dashboard docs | Mock start + link to operator URLs in PR |
| Docker / Infinity Pilot | `docs/operations/INFINITY_PILOT_EARLY_ADOPTER.md` + compose smoke |
| Broad runtime / law | `make infinity1-flagship-verification` (heavy — ask in discussion first) |

Escalation and co-collaboration rules: [`HUMAN_AI_CO_COLLABORATION_CHARTER.md`](HUMAN_AI_CO_COLLABORATION_CHARTER.md).

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

Full operator onboarding: [`docs/operations/FIRST_TIME_OPERATOR_GUIDE.md`](docs/operations/FIRST_TIME_OPERATOR_GUIDE.md)  
Quick start: [`README.md`](README.md#how-to-join-in-10-minutes) — **How to join in 10 minutes** (mock mode)  
Release history: [`CHANGELOG.md`](CHANGELOG.md)

## What not to commit

Local-only artifacts are listed in [`.gitignore`](.gitignore). Never commit:

- ISO images (`*.iso`) or forge output under `wolf-cog-os/output/`
- Wolf-CoG-OS operator backup snapshots under `wolf-cog-os/payload/opt/cogos/memory/backups/`
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
