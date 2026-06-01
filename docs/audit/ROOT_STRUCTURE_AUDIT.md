# AAIS Root Structure Audit

This file is the deliberate top-level inventory for the repository root.

Its job is to answer one practical question:

what should stay visible at the repo root, what should remain local-only, and
what should be reviewed before any future archive move?

If this file conflicts with runtime code, runtime code wins.

## 1. Status Model

Use these buckets for root cleanup decisions:

- `active_core`
  - root items that belong to the live repository shape
- `local_only`
  - generated, runtime, cache, environment, or machine-local material
- `review_first_archive_candidate`
  - older helpers, legacy launchers, reports, or sidecar scripts that may be
    archived later, but should not be moved blindly
- `keep_until_replaced`
  - live or potentially live support surfaces that still need a direct owner
    before relocation

## 2. Active Core Root

These are the roots that clearly belong in the visible repo structure now:

- `README.md`
- `document/law/REPO_LAWBOOK.md`
- `docs/`
- `src/`
- `tests/`
- `app/`
- `frontend/`
- `aais/`
- `api/`
- `data/`
- `control/`
- `evals/`
- `evolve_engine/`
- `forge/`
- `forge_eval/`
- `mobile/`
- `training/`
- `pyproject.toml`
- `requirements.txt`
- `pytest.ini`
- `Makefile`
- `Dockerfile`
- `Dockerfile.frontend`
- `docker-compose.yml`

These items define the live repo shape, runtime, packaging path, or primary
developer workflow.

## 3. Local-Only Root

These items should stay local, generated, or ignored:

- `.runtime/`
- `.pytest_cache/`
- `__pycache__/`
- `build/`
- `dist/`
- `node_modules/`
- `.venv/`
- `.venv-broken-launcher-backup-*`
- `.venv-repair-backup-*`
- `.venv-py314-backup/`
- `.local/`
- `.vs/`
- `.vercel/`
- `env/`
- `tmp/`
- `logs/`
- `*.iso`, `*.iso.sha256`
- `wolf-cog-os/output/`, `wolf-cog-os/artifacts/`
- `.cogos-live-safe-work/`, `.cogos-master-boot-work/`, `.ground-up-work/`
- `ci-artifacts/`, `metal-iso-extract/`, `release/`
- Duplicate imports: `AAIS-main/`, `Aris--main/`, `Project-Infinity-main/`

These are runtime, cache, package-manager, or machine-specific surfaces.

They should not be treated as part of the human-visible project structure.

## 4. Review-First Archive Candidates

These root items read like earlier helper, experiment, or sidecar surfaces.

They may become archive candidates, but only after ownership is checked:

### Legacy Or Transitional Python Surfaces

- `aais_ul.py`
- `angels.py`
- `core.py`
- `god_cli.py`
- `god_dashboard.py`
- `jarvis_modular.py`
- `optimization_analyzer.py`
- `performance_test.py`

### Break-Glass Or Transitional Control Scripts

- `emergency_stop.py`
- `hooks.py`
- `killswitch_gui.py`
- `killswitch_init.py`

### Legacy Setup / Deployment / Upgrade Helpers

- `deploy-aws.sh`
- `deploy-heroku.sh`
- `deploy-to-production.sh`
- `docker-logs.sh`
- `docker-setup.sh`
- `docker-start.sh`
- `docker-stop.sh`
- `setup-advanced-ai.sh`
- `setup-advanced-features.sh`
- `setup-advanced-monitoring.sh`
- `setup-cicd-advanced.sh`
- `setup-cost-optimization.sh`
- `setup-enterprise-features.sh`
- `setup-feature-enhancements.sh`
- `setup-int8-quantization.sh`
- `setup-intelligence-speed.sh`
- `setup-llm-upgrade.sh`
- `setup-mixtral-upgrade.sh`
- `setup-monitoring-alerts.sh`
- `setup-monitoring.sh`
- `setup-performance-advanced.sh`
- `setup-performance.sh`
- `setup-scalable-architecture.sh`
- `setup-security.sh`
- `setup-ultra-high-performance.sh`
- `setup-ultra-performance.sh`

### Legacy Start Wrappers And One-Off Launchers

- `start_evolve_engine.py`
- `start_forge.py`
- `start_forge_eval.py`
- `start_jarvis.py`
- `start-personal.ps1`
- `stop-personal.ps1`
- `verify-python-runtime.ps1`
- `preflight.ps1`
- `rotate-openrouter-key.ps1`

These may still be useful, but they are exactly the kind of root clutter that
should be reviewed before deciding whether they stay live, move under a more
owned folder, or get archived later.

## 5. Keep Until Replaced

These root files may still be active support surfaces even if they look noisy:

- `.gitignore`
- `.dockerignore`
- `.vercelignore`
- `.python-version`
- `.gitlab-ci-advanced.yml`
- `MANIFEST.in`
- `nginx.conf`
- `vercel.json`
- `requirements-advanced.txt`
- `requirements-laptop.txt`
- `requirements-local.txt`
- `requirements-training.txt`
- `run-performance-tests.sh`
- `review-documentation.sh`
- `start_jarvis.spec`

They should not be moved until a clearer owning path exists.

## 6. Safe Next Physical Move

The next safe physical cleanup after this audit is not a blind root sweep.

It is:

1. keep the active core visible
2. keep local-only material ignored and local
3. choose one reviewed category of archive candidates at a time
4. move only those reviewed items into a real archive path with a README

Recommended first reviewed archive bucket:

- legacy setup and upgrade shell scripts

That bucket is high-clutter, lower-authority, and easier to isolate than core
Python entrypoints.

Current state:

- completed
- moved to `archive/legacy-root-scripts/`

Recommended second reviewed archive bucket:

- unreferenced transitional root Python files

Current state:

- completed
- moved to `archive/transitional_python/`
- included `aais_evolving_protocol.py`, `aais_provider_fabric.py`,
  `aais_runtime.py`, and `nova_anchors_and_membranes.py`

## 7. Already True After This Pass

- root zip bundles are no longer loose at the repo root
- active docs, archive docs, and future docs are now separated
- local-only runtime and generated folders are explicitly ignored
- legacy setup and deploy shell helpers are no longer loose at the repo root
- unreferenced transitional Python experiments are no longer loose at the repo
  root

This means the next cleanup can be surgical instead of exploratory.
