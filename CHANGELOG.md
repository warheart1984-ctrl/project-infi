# Changelog

All notable changes to the **AAIS Python runtime and operator surfaces** are documented here.

Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).  
This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

CoGOS ISO releases are tracked separately — see [docs/releases/README.md](docs/releases/README.md).

## [Unreleased]

### Added

- (none yet)

## [0.3.0] - 2026-06-02

Audit Alt-3 — Recipe Module, Imagine Generator, and Human Voice Extraction promoted from concept to **partial live**, with capability bridge catalog, UL lineage hooks, and env-gated Grok imagine rendering.

### Added

- **Recipe Module** — governed recipe packs, `mission_board.create_from_recipe`, `POST /api/jarvis/missions/from-recipe`, capability bridge `recipe_module` / `create_mission`, fixture `tools/recipe/fixtures/onboarding-v1.json`
- **Imagine Generator** — pattern emit, Story Forge admission handoff, `POST /api/jarvis/imagine/emit` and `/handoff`, capability bridge `imagine_generator` / `emit`, `handoff`, `grok_render`
- **Human Voice Extraction** — extract / signoff / Speakers constraints handoff (no raw notes persisted), human-voice API, capability bridge `human_voice_extraction` / `extract`, `signoff`, `handoff`
- **Alt-3 deferred wiring** — `src/alt3_lineage.py` subsystem-specific UL lineage; `src/imagine_grok.py` with env-only xAI keys (`STORY_FORGE_XAI_API_KEY`, `XAI_API_KEY`); `GET /api/jarvis/imagine/keys-status`, `POST /api/jarvis/imagine/grok-render` (428 `keys_required` when unset)
- **Governance** — SSP concept bundles for all three families; `make alt3-gate`, `recipe-module-gate`, `imagine-generator-gate`, `human-voice-extraction-gate`, `ssp-gate`, `genome-gate`; proof packets under `docs/proof/platform/`, `docs/proof/storyforge/`, `docs/proof/speakers/`
- **SSP Alt-4** — subsystem genome meta-schema, promotion/retirement/mutation protocols, genome registry (`governance/`)

### Changed

- `docs/runtime/AAIS_SUBSYSTEM_SPEC.md` — §8 partial-live entries for Recipe Module, Imagine Generator, Human Voice Extraction
- `docs/operations/FIRST_TIME_OPERATOR_GUIDE.md` — Grok API key paragraph for imagine render
- Capability bridge catalog extended in `src/capability_service_bridge.py`

### Security

- Grok/xAI API keys are read **only** from environment variables — no per-request key override, no persistence in artifacts (hashes only in `grok_render.json`)

### Verification (v0.3.0)

```bash
make alt3-gate
python -m pytest tests/test_recipe_module.py tests/test_imagine_generator.py tests/test_human_voice_extraction.py -q
python -m pytest tests/test_capability_bridge_alt3.py tests/test_alt3_lineage.py tests/test_imagine_grok.py -q
python tools/governance/check_ssp_completeness.py
```

[0.3.0]: https://github.com/warheart1984-ctrl/Project-Infinity1/releases/tag/v0.3.0

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
