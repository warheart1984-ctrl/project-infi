# Readiness 82 → 91 Fix Report

**Date:** 2026-06-05  
**Authority:** Readiness plan `82_to_91_readiness`  
**Outcome:** Readiness estimate **91 / 100** (governed MVP; not flagship GA)

---

## Summary

This pass closed the final naming-genome warning, completed pilot GA operator verification (OpenRouter hygiene, frontend/mobile gates), and reconciled trust-bundle evidence. Nine points remain to 100: full pytest cross-host (+8) and final GA claim reconciliation (+1).

| Phase | Work | Points | Cumulative |
|-------|------|--------|------------|
| Today | `aris_standalone_service` SSP header closure | +3 | **85** |
| This week | OpenRouter hygiene + frontend/mobile pilot gates | +6 | **91** |

---

## 1. SSP linguistic closure — `aris_standalone_service` header

### What was fixed

Added dual naming headers to `aris_service/__init__.py`:

```python
# Mythic: Aris Standalone Service
# Engineering: ArisStandaloneServiceEngine
```

### Why

`governance/subsystem_genomes/aris_standalone_service.genome.v1.json` declares `ssp.engineering_class: ArisStandaloneServiceEngine` and lists `aris_service/__init__.py` as the **first** `runtime.surface` module. `tools/governance/check_naming_genome.py` inspects only that first module path. Without headers, the gate reported the sole remaining warning (193 → 1 → **0**).

Note: `src/aris_service_client.py` already had `# Engineering: ArisServiceClientEngine` but is the **second** module surface and does not satisfy the gate.

### How

1. Inserted headers immediately after the module docstring in `aris_service/__init__.py`.
2. Verified:
   ```bash
   python tools/governance/check_naming_genome.py --snapshot
   python tools/governance/check_naming_genome.py --strict
   ```
   Expected and observed: **0 warnings**, exit 0 on strict.

### Evidence

- `docs/trust_bundles/2026-06-05-flagship-v1.26.1-readiness.md` (bumped 82 → 85, then 91)
- `docs/audit/AAIS_STATUS_AUDIT.md` §7
- `docs/audit/LOGBOOK.md` — SSP linguistic closure entry

---

## 2. OpenRouter key hygiene (operator verification)

### What was fixed

Documented and verified OpenRouter secret posture; no live keys in repo or environment.

### Why

Pilot GA hardening requires operator proof that OpenRouter credentials are not leaked in tracked files and that rotation tooling is ready when routing is enabled.

### How

1. `powershell -File tools/ops/rotate-openrouter-key.ps1 -VerifyOnly` — no `OPENROUTER_API_KEY` in `.env`, process, user, or machine env.
2. `git grep -i "sk-or-"` — only doc examples in archive/checklist; no live keys.
3. Archived masked log: `.runtime/pilot-ga-openrouter-verify.log` (gitignored; referenced from trust bundle).

**Operator follow-up when OpenRouter is enabled:** create dashboard key → `-NewKey "<key>"` → restart AAIS → smoke one turn → revoke prior key.

---

## 3. Frontend re-verification

### What was fixed

Fresh `npm ci` on Windows native Node; full pilot gate transcript archived.

### Why

Prior baseline (2026-04-29): 47 tests passed, 0 prod audit vulns. Pilot GA checklist required re-run on a Node-equipped host. Initial attempts failed:
- **WSL on `/mnt/e/`:** `npm ci` EPERM on symlinks (Windows mount limitation).
- **Stale `node_modules` on Windows:** vitest `ERR_PACKAGE_PATH_NOT_EXPORTED` for `vitest/vitest.mjs` until clean reinstall.

### How

Host: **Windows native Node v24.16.0 / npm 11.13.0**

```bash
cd frontend
rm -rf node_modules   # WSL or PowerShell
npm ci
npm run test:ci
npm run build
npm run audit:prod
```

| Gate | Result |
|------|--------|
| `test:ci` | **30 passed** (8 files) — exit 0 |
| `build` | exit 0 |
| `audit:prod` | exit 1 — 3 prod vulns (axios, react-router) |

Log: `.runtime/pilot-ga-frontend-v1.log`

**Regression note:** prod audit reports 3 vulnerabilities vs April baseline of 0. Tracked as asserted debt in trust bundle; not remediated in this pass (out of scope for readiness score, in scope for GA).

---

## 4. Mobile re-verification + missing API module

### What was fixed

- Restored `mobile/src/lib/api.ts` (axios client, `apiBaseUrl`, `visionToolsEnabled`, `getApiErrorMessage`).
- Added `.gitignore` exception so `mobile/src/lib/**` is tracked (`lib/` global rule had excluded it).
- Mobile `typecheck` passes.

### Why

Three screens import `../lib/api` but the module was absent from the repo:

- `ImageAnalyzerScreen.tsx`
- `ImageGeneratorScreen.tsx`
- `TextGeneratorScreen.tsx`

`npm run typecheck` failed with `TS2307: Cannot find module '../lib/api'`.

The module contract is documented in `mobile/README.md` via `EXPO_PUBLIC_API_URL` and `EXPO_PUBLIC_ENABLE_VISION_TOOLS`.

### How

1. Created `mobile/src/lib/api.ts` matching screen imports and README env conventions.
2. Updated `.gitignore`:
   ```
   !mobile/src/lib/
   !mobile/src/lib/**
   ```
3. Ran on Windows native Node:
   ```bash
   cd mobile
   npm ci
   npm run typecheck
   npm audit --omit=dev
   ```

| Gate | Result |
|------|--------|
| `typecheck` | exit 0 |
| `audit --omit=dev` | exit 1 — 3 vulns (axios, ws, brace-expansion) |

Log: `.runtime/pilot-ga-mobile-v1.log`

---

## 5. Trust bundle and checklist reconciliation (85 → 91)

### What was fixed

- `docs/trust_bundles/2026-06-05-flagship-v1.26.1-readiness.md` — score **91/100**, pilot proof links, stale asserted rows cleaned.
- `docs/audit/PILOT_GA_HARDENING_CHECKLIST.md` — OpenRouter hygiene, frontend/mobile, naming-genome 0 warnings marked proven.
- `docs/audit/LOGBOOK.md` — pilot GA operator verification entry.

### Why

Phase 2 items were duplicated or still marked asserted after being proven. Pending blockers listed resolved items (193 warnings, recipe drift, OTEM deferred).

### How

Moved proven items to a dedicated pilot verification table; retained only true GA blockers:

1. Full pytest cross-host on independent physical machine.
2. Production npm audit remediation.
3. OpenRouter key apply + smoke when operator enables routing.

---

## Artifacts (operator-local, gitignored)

| Artifact | Purpose |
|----------|---------|
| `.runtime/pilot-ga-openrouter-verify.log` | OpenRouter VerifyOnly transcript |
| `.runtime/pilot-ga-frontend-v1.log` | Frontend test/build/audit transcript |
| `.runtime/pilot-ga-mobile-v1.log` | Mobile typecheck/audit transcript |

Referenced from trust bundle `proof_links`; reproduce with commands in `PILOT_GA_HARDENING_CHECKLIST.md`.

---

## Remaining for 100 (out of scope)

| Item | Points |
|------|--------|
| Full `python -m pytest -q` on independent physical host | +8 |
| Final GA trust-bundle claim + npm audit debt cleared | +1 |

Runbook: `docs/proof/aais-ul/FLAGSHIP_CROSS_MACHINE_MATRIX.md`

---

## Quick reproduction

```bash
# SSP closure
python tools/governance/check_naming_genome.py --snapshot
python tools/governance/check_naming_genome.py --strict

# OpenRouter hygiene
powershell -File tools/ops/rotate-openrouter-key.ps1 -VerifyOnly
git grep -i "sk-or-"

# Frontend (Windows native Node >= 18)
cd frontend && npm ci && npm run test:ci && npm run build && npm run audit:prod

# Mobile
cd mobile && npm ci && npm run typecheck && npm audit --omit=dev
```
