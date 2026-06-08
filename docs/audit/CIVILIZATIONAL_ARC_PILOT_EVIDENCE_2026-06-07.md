# Civilizational Arc — Pilot Evidence (2026-06-07)

CISIV stage: **verification (external federation)**

Maps tier-specific bullets from [`CIVILIZATIONAL_ARC_PROVEN_SIGNOFF.md`](./CIVILIZATIONAL_ARC_PROVEN_SIGNOFF.md) to concrete tests, gates, and federation chaos artifacts for Releases **45–48** (Stages **15–18**).

## Cross-tier evidence

| Sign-off domain | Evidence |
|-----------------|----------|
| Internal gates | `ci-artifacts/civilizational_arc_proven_gate_2026-06-07.txt` — four body gates PASS + pytest |
| Full civilizational pytest | `ci-artifacts/civilizational_arc_proven_pytest_2026-06-07.txt` — **24 passed**, 1 skipped (live chaos when AAIS down) |
| Charter Art IV / V | `tests/test_human_ai_charter_surfaces.py`; ISD/NFD observe tests assert `charter_surfaces.epistemic_perimeter` (Art IV) and `collaboration_options` (Art V, ≥2 options) |
| Dual-gate block | Runtime: `operator_approved` guard in `inter_substrate_diplomacy_runtime.py`; chaos adopt abuse `operator_approved: false` → 403 in `tools/stress/federation_chaos_hammer.py` |
| External legibility | [`FEDERATION_CHAOS_RUN_2026-06-07.md`](./FEDERATION_CHAOS_RUN_2026-06-07.md) — 92 probes, Phase C UGR cross-tenant (`tenant:contoso` peer step in `test_ugr_federation_mission_builder`) |
| Rollback | [`CIVILIZATIONAL_ARC_ROLLBACK.md`](./CIVILIZATIONAL_ARC_ROLLBACK.md) |
| Nova interpret-only | [`docs/subsystems/nova/README.md`](../subsystems/nova/README.md) — Nova does not adopt civilizational overlays without Jarvis path |

**Fresh live federation chaos:** not re-run at sign-off (AAIS not reachable on `127.0.0.1:8000`). Prior pilot run + offline hammer module tests (`tests/test_federation_chaos_hammer.py`) satisfy external legibility for promotion.

## Stage 15 — Inter-Substrate Diplomacy (Release 45)

| Criterion | Evidence |
|-----------|----------|
| External peer / substrate scopes | `tests/test_inter_substrate_diplomacy_adopt.py` candidate `substrate_scopes`: `ul_substrate`, `memory_overlay`, `imxp_envelope` |
| Accord legibility | Registry schema `operator_diplomatic_accord.v1`; adopt writes governance registry + `jarvis_memory_board_diplomacy.v1.json` |
| No execution bypass | Body gate: `tools/governance/run_inter_substrate_diplomacy_body_verification.py` |
| Chaos Phase A/B | Federation chaos GET `/api/operator/diplomacy`, `/api/operator/diplomacy/accords`; adopt abuse matrix per subsystem |

## Stage 16 — Norm Federations (Release 46)

| Criterion | Evidence |
|-----------|----------|
| Multi-norm treaty | `tests/test_norm_federation_adopt.py` — `adopted_norm_ids`: `norm_a`, `norm_b` |
| Federation drift | `tests/test_norm_federation_observe.py` — `observe_federation_drift`, ISD-0-style read-only observe |
| Charter refs on observe | NFD observe snapshot includes `charter_surfaces` (Art IV/V) via `norm_federation_runtime` |
| Chaos | Phase A GET norm-federation routes; Phase B observe/adopt abuse |

## Stage 17 — Constitutional Evolution (Release 47)

| Criterion | Evidence |
|-----------|----------|
| Amendment trail | `tests/test_constitutional_evolution_adopt.py` — dual-gate adopt, `adopted_amendments()` count |
| Blocked without approval | Runtime dual gate; chaos `not_approved` adopt case expects 403 |
| Art VII parity | Observe → drift → operator + Jarvis adopt path in CEV runtime (CEV-0 / CEV-2 classes in tests) |

## Stage 18 — Governed Civilization (Release 48)

| Criterion | Evidence |
|-----------|----------|
| Multi-charter registry | `tests/test_governed_civilization_adopt.py` — `admitted_charter_ids`: `charter_a`, `charter_b` |
| GCV-3 read-only elevation | Contract [`GOVERNED_CIVILIZATION_CONTRACT.md`](../contracts/GOVERNED_CIVILIZATION_CONTRACT.md) GCV-3; observe tests assert GCV-0 with **no overlay write** (`test_observe_without_overlay_write`) |
| Capstone fusion | `make civilizational-arc-gate` aggregates ISD/NFD/CEV/GCV body verification |
| Chaos | Phase A GET civilization routes; Phase B governed-civilization abuse |

## Reproduction

```powershell
cd e:\project-infi
python -m pytest tests/test_human_ai_charter_surfaces.py tests/test_inter_substrate_diplomacy_observe.py tests/test_norm_federation_observe.py tests/test_inter_substrate_diplomacy_adopt.py tests/test_norm_federation_adopt.py tests/test_constitutional_evolution_observe.py tests/test_constitutional_evolution_adopt.py tests/test_governed_civilization_observe.py tests/test_governed_civilization_adopt.py tests/test_federation_chaos_hammer.py -q
python tools/governance/run_inter_substrate_diplomacy_body_verification.py
python tools/governance/run_norm_federation_body_verification.py
python tools/governance/run_constitutional_evolution_body_verification.py
python tools/governance/run_governed_civilization_body_verification.py
```

Optional live chaos (when AAIS mock is up):

```powershell
python -m aais start --data-dir ./.runtime/aais-data --preset mock --no-browser
python tools/stress/federation_chaos_hammer.py
```
