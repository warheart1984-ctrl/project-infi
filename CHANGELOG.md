# Changelog

All notable changes to the **AAIS Python runtime and operator surfaces** are documented here.

Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).  
This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

CoGOS ISO releases are tracked separately — see [docs/releases/README.md](docs/releases/README.md).

## [Unreleased]

### Added

- (none yet)

## [1.1.0] - 2026-06-02 — Infinity 1 (complete)

**Infinity 1 (complete)** — thirteen governed subsystem genomes, Alt-5 waves 1–2 (four organs at `governed`), barebones summon wave (bridge, memory board, governed pipeline), and reproducible promotion scripts.

### Added

- **Alt-5 Summon Wave 2** — `reflection_runtime_organ`, `memory_runtime_organ` at `governed`; `GET /api/jarvis/reflection-runtime/status`, `GET /api/jarvis/memory-runtime/status`; `tools/governance/alt5_promote_wave2_mvp.py`
- **Alt-5 governed promotion** — all four Alt-5 organs (`safety_envelope_organ`, `operator_profile_organ`, reflection, memory) at `governed`; `tools/governance/alt5_promote_governed.py`
- **Barebones summon wave** — `capability_service_bridge`, `jarvis_memory_board`, `governed_direct_pipeline` at `governed`; status APIs and `make barebones-gate`; `tools/governance/barebones_promote_governed.py`
- **Governance gates** — `reflection-runtime-gate`, `memory-runtime-gate`, capability-bridge, memory-board, governed-pipeline checks

### Changed

- Thirteen registered subsystem genomes (all at `governed`); [AAIS_SUBSYSTEM_SPEC.md](docs/runtime/AAIS_SUBSYSTEM_SPEC.md) §8 constitutional layer extended
- [AAIS_SSP_PROTOCOL.md](docs/contracts/AAIS_SSP_PROTOCOL.md) — Alt-5 wave 2 + governed promotion path
- `make alt5-gate` includes wave 2 organ gates

### Verification (v1.1.0)

```bash
make genome-gate alt4-gate alt5-gate barebones-gate tier5-gate
python -m pytest tests/test_safety_envelope_organ.py tests/test_operator_profile_organ.py \
  tests/test_reflection_runtime_organ.py tests/test_memory_runtime_organ.py \
  tests/test_governance_organs_alt4.py tests/test_adaptive_governance.py -q
python tools/governance/alt5_promote_governed.py  # idempotent when already governed
```

[1.1.0]: https://github.com/warheart1984-ctrl/Project-Infinity1/releases/tag/v1.1.0

## [1.0.0] - 2026-06-02 — Infinity 1

**Infinity 1** — self-governing runtime: Alt-4 lifecycle organs, constitutional layer (six governed genomes), Alt-5 summon wave (two new organs), Governance Tier 5 adaptive layer.

### Added

- **Alt-4 Runtime Organs** — `src/governance_organs/` (Genome, Promotion, Mutation, Retirement engines); boot hooks in `src/api.py` and `app/main.py`; capability-bridge DNA enforcement; `make alt4-gate`, `promotion-scan`, `promotion-apply`; MP-NTP-001 golden mutation path; [AAIS_ALT4_RUNTIME_OPERATOR_GUIDE.md](docs/contracts/AAIS_ALT4_RUNTIME_OPERATOR_GUIDE.md)
- **Governed Subsystem Expansion** — all six original genomes at `governed` (lineage console, triangulation, NTP, recipe, imagine, human voice)
- **Alt-5 Summon Wave** — `safety_envelope_organ`, `operator_profile_organ` at MVP; `GET /api/jarvis/safety-envelope/status`, `GET /api/jarvis/operator-profile`; `make alt5-gate`
- **Governance Tier 5** — [AAIS_ADAPTIVE_GOVERNANCE.md](docs/contracts/AAIS_ADAPTIVE_GOVERNANCE.md), `AdaptiveEngine`, `make tier5-gate`, contextual gates on capability bridge; `recipe_module` pilot

### Changed

- Eight registered subsystem genomes (six governed + two Alt-5 MVP); [AAIS_SUBSYSTEM_SPEC.md](docs/runtime/AAIS_SUBSYSTEM_SPEC.md) §8 constitutional layer
- [AAIS_SSP_PROTOCOL.md](docs/contracts/AAIS_SSP_PROTOCOL.md) — Alt-4 runtime organs + Alt-5 summon wave sections

### Verification (v1.0.0)

```bash
make genome-gate alt4-gate alt5-gate tier5-gate
python -m pytest tests/test_governance_organs_alt4.py tests/test_adaptive_governance.py tests/test_safety_envelope_organ.py tests/test_operator_profile_organ.py -q
```

[1.0.0]: https://github.com/warheart1984-ctrl/Project-Infinity1/releases/tag/v1.0.0

## [0.4.0] - 2026-06-02

Three Ideas MVP — CISIV Lineage Console, Forensic Triangulation Ledger, and Narrative Trust Pack promoted from concept to **partial live**.

### Added

- **CISIV Lineage Console** — `src/ul_lineage.py`, emitter hooks (chat, memory, capability, forge), `GET /api/jarvis/lineage/<mission_id>`, Operator CISIV Lineage panel, `tools.ul.smoke --lineage-graph`, `tools.ul.drift --lane lineage`
- **Forensic Triangulation** — `triangulation/` package, `python -m triangulation correlate`, fixture `tri-demo-001`, bridge map GOV-CI-03 ↔ fd_flow, `make triangulation-gate`
- **Narrative Trust Pack** — `src/capabilities/narrative_trust_pack.py`, `python -m tools.narrative pack|verify|signoff`, E2E + tamper tests, `make narrative-gate`
- **Proof packets** — `docs/proof/aais-ul/UL_LINEAGE_CONSOLE_V1_PROOF.md`, `docs/proof/forensics/TRIANGULATION_V1_PROOF.md`, `docs/proof/storyforge/NARRATIVE_TRUST_PACK_V1_PROOF.md`
- **Docs** — active runtime/subsystem docs; `docs/_future/ideas_pending/` concept specs updated to implementation stage

### Changed

- `docs/runtime/AAIS_SUBSYSTEM_SPEC.md` — §8 Three Ideas MVP partial-live table
- `README.md` — v0.4.0 release section and verification commands

### Verification (v0.4.0)

```bash
make lineage-gate triangulation-gate narrative-gate
python -m pytest tests/test_ul_lineage.py tests/test_triangulation.py tests/test_narrative_trust_pack.py -q
python -m tools.ul.smoke --lineage-graph tools/ul/fixtures/lineage_multi_hop.json --no-pytest
```

[0.4.0]: https://github.com/warheart1984-ctrl/Project-Infinity1/releases/tag/v0.4.0

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
