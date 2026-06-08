# Chaos sweep — 2026-06-07

Target: live AAIS at `http://127.0.0.1:8000` (health 200 pre/post sweep).

Artifacts: `ci-artifacts/chaos_sweep_2026-06-07_*`

## Summary

| Vector | Result | Key metric |
|--------|--------|------------|
| Live API stress (normal) | **PASS** | 625/625 OK, 0×5xx, p95 1769ms |
| Live API stress (high-conc 16×5) | **PASS** | 625/625 OK, 0×5xx, p95 939ms |
| OTEM approval smoke | **PASS** | Level-10 approve path, 0×5xx |
| Adversarial chaos-check (Forgekeeper/Mechanic/Scorpion) | **PASS** | 14 passed |
| OTEM/safety pytest slice | **PASS** | 21 passed |
| Stress/governance pytest slice | **FAIL** | 11 failed, 40 passed |
| Chaos hammer | **FAIL (crash)** | Died at step 8 importing `src.api` — genome boot |
| Seam discovery (live + offline) | **FAIL (crash)** | Same genome boot on route harvest |
| Alt-4 gate | **FAIL** | Body-runtime genome registry invalid |
| Immune resilience organ gate | **PASS** | pytest slice green |

**Server survived:** health 200 after all live HTTP abuse. No 5xx under live_api_stress.

## Live stress — held

Both `live_api_stress.py` runs completed cleanly:

- 11 operator endpoints + 102 subsystem status endpoints + chat sessions
- 625 requests each run, **0 errors/5xx**
- High-concurrency rerun improved p95 (1769ms → 939ms)

OTEM approval smoke completed without server errors.

## Breakage found

### 1. Body-runtime genome registry (blocker)

`GenomeEngine.reload()` → `ok False`. Blocks:

- `chaos_hammer.py` (status farm imports `src.api`)
- `seam_discovery_stress.py` (even `--offline` harvests Flask routes via `src.api`)
- `alt4_gate.py` and `test_governance_organs_alt4.py` (4 failures)

Representative errors:

```
constitutional_ecosystem_runtime.genome.v1.json: missing mutation.history
social_continuity_runtime: parent identity_self_model_runtime does not list social_continuity_runtime in children
… (full chain of body-runtime lineage reciprocity gaps)
```

This is a **new/different** cluster from the immune_resilience fix applied earlier today.

### 2. Coherence fabric pipeline mocks (2 failures)

`test_coherence_fabric_pipeline.py` — expects `BLOCK`, gets `ALLOW` (mock binding drift).

### 3. Forge gates (3 failures)

`test_forge_shippable_gate.py`, `test_forge_platform_gate.py` — ISO smoke / promotion fixture blockers (Windows/local env).

### 4. Jarvis protocol modular provider (2 failures)

Preview/modules routing — workspace context vs governance coherence module mismatch.

## Chaos hammer (partial)

Completed steps 1–7 (malformed JSON, traversal, wrong methods, UGR abuse, OTEM bypass, 24 concurrent sessions) before crashing on status-farm route discovery. Prior artifact `ci-artifacts/chaos_hammer_report.json` shows 222 probes / 0×5xx from an earlier run; **this sweep run did not finish**.

## Recommended next fixes (priority)

1. ~~**Body-runtime genome closure**~~ **RESOLVED (2026-06-07)** — added `mutation.history`, fixed parent/child reciprocity across 10 body-runtime genomes. `GenomeEngine.reload()` → ok True; alt4 gate PASS; seam discovery offline PASS; chaos hammer completes (223 probes, 0×5xx).
2. **Pipeline mock binding** — fix `test_coherence_fabric_pipeline.py` patch targets.
3. **Forge gate fixtures** — refresh Windows-local ISO/promotion artifacts or mark env-dependent.
4. **Jarvis protocol modular provider** — align preview module routing with workspace context expectations.

## Re-run command (after genome fix)

```powershell
cd e:\project-infi
python tools/stress/live_api_stress.py
python tools/stress/chaos_hammer.py
python tools/stress/seam_discovery_stress.py
python tools/stress/otem_approval_smoke.py
python -m pytest tests/test_seam_discovery_stress.py tests/test_governance_organs_alt4.py -q
```
