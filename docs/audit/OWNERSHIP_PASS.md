# Ownership Pass

Fast ownership cut for the current repo layout.

## Canonical Entry Truth

- There is no root `run.py` or root `main.py`.
- Live runtime entry ownership is currently split across:
  - `app/main.py` -> workflow shell
  - `src/api.py` -> live API/runtime surface
  - `aais/__main__.py` + `aais/launcher.py` -> packaged CLI launcher
- Root `start_*.py` files are launcher shims, not canonical runtime truth.

## Quick Table

| File / Pattern | Owner | Action |
| --- | --- | --- |
| `app/main.py` | runtime | KEEP |
| `src/api.py` | runtime | KEEP |
| `aais/__main__.py` | packaging | KEEP |
| `aais/launcher.py` | packaging/runtime | KEEP |
| `docker-compose.yml` | infra | KEEP |
| `Dockerfile`, `Dockerfile.frontend`, `nginx.conf`, `Makefile` | infra | KEEP |
| `pyproject.toml`, `MANIFEST.in`, `requirements*.txt` | packaging | KEEP |
| `training/train_jarvis_lora.py` | pipeline | KEEP in `training/` |
| `training/prepare_messages_dataset.py` | pipeline | KEEP in `training/` |
| `src/entrypoints/start_jarvis.py` | runtime launcher | KEEP in `src/entrypoints/` |
| `tools/services/start_forge.py`, `tools/services/start_forge_eval.py`, `tools/services/start_evolve_engine.py` | service launchers | KEEP in `tools/services/` |
| `god_cli.py` | tools / legacy | ARCHIVE after grep |
| `god_dashboard.py` | tools / legacy | ARCHIVE after grep |
| `core.py`, `angels.py` | legacy runtime | ARCHIVE after grep |
| root doctrine/helper duplicates (`aais_ul.py`, `angels_and_wards.py`, `six_wards_guardrails.py`, `writers_3_rules.py`, `jarvis_modular.py`) | legacy root copies | ARCHIVE after grep |
| `optimization_analyzer.py`, `performance_test.py`, `locustfile.py`, `run-performance-tests.sh` | perf tooling | MOVE to `tools/perf/` |
| `tools/ops/review-documentation.sh`, `tools/ops/preflight.ps1`, `tools/ops/verify-python-runtime.ps1`, `tools/ops/rotate-openrouter-key.ps1` | developer tools | KEEP in `tools/ops/` |
| `tools/ops/emergency_stop.py`, `tools/ops/killswitch_gui.py`, `tools/ops/killswitch_init.py`, `tools/ops/hooks.py`, `tools/ops/start-personal.ps1`, `tools/ops/stop-personal.ps1` | ops / kill-switch / control | KEEP in `tools/ops/` |
| canonical doctrine/runtime modules in `src/` (`src/aais_ul.py`, `src/angels_and_wards.py`, `src/six_wards_guardrails.py`, `src/writers_3_rules.py`, `src/jarvis_modular.py`) | runtime support | KEEP in `src/` |
| `demo_output.txt` | artifact | ARCHIVE |
| unknown one-off root scripts | unknown | ARCHIVE after grep |

## Decisive Calls

### Keep At Root

- infra and packaging only
- specifically:
  - `docker-compose.yml`
  - `Dockerfile*`
  - `Makefile`
  - `pyproject.toml`
  - `MANIFEST.in`
  - `requirements*.txt`
  - top-level repo docs and config files

### Move Out Of Root

Create these destinations:

- `src/entrypoints/`
  - `start_jarvis.py`
- `tools/services/`
  - `start_forge.py`
  - `start_forge_eval.py`
  - `start_evolve_engine.py`
- `tools/perf/`
  - `optimization_analyzer.py`
  - `performance_test.py`
  - `locustfile.py`
  - `run-performance-tests.sh`
- `tools/ops/`
  - `review-documentation.sh`
  - `preflight.ps1`
  - `verify-python-runtime.ps1`
  - `rotate-openrouter-key.ps1`
  - `start-personal.ps1`
  - `stop-personal.ps1`
  - kill-switch/control helpers

### Archive Candidates

These look like legacy or orphaned root artifacts and should not stay in the root namespace:

- `god_cli.py`
- `god_dashboard.py`
- `core.py`
- `angels.py`
- root doctrine/helper duplicates now superseded by `src/` versions
- `demo_output.txt`

Archive only after a final reference grep confirms no live imports or launch paths depend on them.

## Immediate Recommendation

If doing this in two passes:

1. Root hygiene pass
   - create `src/entrypoints/`, `tools/services/`, `tools/perf/`, `tools/ops/`
   - move the obvious non-runtime root scripts out of root

2. Legacy isolation pass
   - grep and archive `god_*`, `core.py`, `angels.py`, and root `jarvis_modular.py`

## Rule

Root should own only:

- packaging
- infra
- top-level docs
- minimal launch metadata

Everything else should live under a named subsystem, tool domain, or archive boundary.
