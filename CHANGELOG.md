# Changelog

All notable changes to the **AAIS Python runtime and operator surfaces** are documented here.

Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).  
This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

CoGOS ISO releases are tracked separately — see [docs/releases/README.md](docs/releases/README.md).

## [Unreleased]

### Added

- (none yet)

## [0.2.0] - 2026-06-02

Initial public release of Project Infinity / AAIS as an Apache 2.0 monorepo.

### Added

- Cross-platform launcher (`python -m aais start | prepare | doctor`)
- FastAPI workflow shell with packaged React operator UI (`app/`, `frontend/`)
- Jarvis cognition runtime with UL substrate, Project Infi law, and CISIV staging (`src/`)
- Provider registry: mock, laptop, local, OpenAI, Anthropic, OpenRouter routes
- Optional forge/evolve contractor lanes (`forge/`, `forge_eval/`, `evolve_engine/`)
- Platform Membrane multi-tenant ops ingress (`platform/`)
- Infinity Pilot Docker stack (`deploy/pilot/`)
- Wolf-CoG-OS ISO/rootfs forge scripts (`wolf-cog-os/`)
- UL drift/smoke tooling (`tools/ul/`)
- Governance CI gates (CoGOS CI, UGR trust bundle, documentation baseline, Forgekeeper, Scorpion, repo hygiene)
- First-Time Operator Guide and architecture README sections
- Apache 2.0 [LICENSE](LICENSE), [SECURITY.md](SECURITY.md), root [.env.example](.env.example)

### Changed

- README restructured with architecture diagram, tiered entry paths, and expanded repo layout
- Repo hygiene enforced via `check-repo-hygiene.py` and `REPO_HYGIENE_MANIFEST.json`

### Fixed

- Detachment guard exposed through governed read/clear API routes with regression coverage
- Ingress route identity preserved across message, stream, and compat lanes

### Security

- Removed tracked Wolf-CoG-OS operator backup bundles containing development signing keys
- Added `.gitignore` rule for `wolf-cog-os/payload/opt/cogos/memory/backups/*`
- Documented production hardening checklist in SECURITY.md

### Known limits

- Infinity Pilot is early-adopter, not GA — see [INFINITY_PILOT_BASELINE_CHECKLIST.md](docs/baseline/INFINITY_PILOT_BASELINE_CHECKLIST.md)
- Scorpion operational runbook is a skeleton
- Platform OIDC and multi-tenant K8s hardening partially open
- CoGOS ISO promotion requires GitHub Actions minisign secrets (not in repo)

### Verification (v0.2.0)

```bash
python -m pytest tests/test_cisiv.py tests/test_chat_turn_governance.py -q
python -m tools.ul.smoke
curl -fsS http://127.0.0.1:8000/health
make stack-pilot-gate   # Tier 2 Infinity Pilot only
```

[0.2.0]: https://github.com/warheart1984-ctrl/Project-Infinity1/releases/tag/v0.2.0
