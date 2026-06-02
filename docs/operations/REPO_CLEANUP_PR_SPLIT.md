# Repo Cleanup PR Split

Use this map to land the commit wave as four focused pull requests after Repo Steward infrastructure merges.

## PR-A — Gates and production hardening CI

| Path | Notes |
|------|-------|
| `.github/workflows/repo-hygiene-gate.yml` | New |
| `.github/workflows/stack-closure-gate.yml` | If present locally |
| `.github/workflows/governance-ledger-gate.yml` | If present locally |
| `.github/workflows/slingshot-governance-gate.yml` | If present locally |
| `.github/workflows/pytest-smoke.yml` | If present locally |
| `.github/scripts/check-repo-hygiene.py` | New |
| `.github/scripts/check-canonical-lane-sync.py` | New |
| `.github/scripts/check-consentful-inference.py` | If present locally |
| `.github/scripts/check-lab-cross-machine.py` | If present locally |
| `.github/scripts/validate-proof-bundle.py` | If present locally |
| `.github/scripts/check-forge-shippable-gate.py` | Repo hygiene embed |
| `.github/governance/command-ledger.json` | Repo steward entries |
| `Makefile` | `repo-hygiene-gate`, `production-hardening-gate`, `REPO_HYGIENE_MODE` |
| `tests/test_check_repo_hygiene_script.py` | New |
| `tests/test_consentful_inference.py` | If present locally |
| `tests/test_lab_replay.py` | If present locally |
| `tests/test_slingshot_e2e_fixture.py` | If present locally |

Verify: `make repo-hygiene-gate`, `make production-hardening-gate` (when wired)

## PR-B — Synthetic Mind and cog_runtime

| Path | Notes |
|------|-------|
| `src/cog_runtime/**` | Canonical runtime source |
| `scripts/cogos/**` | Bundle builder |
| `ai_factory/synthetic_mind_deploy.py` | If present locally |
| `platform/synthetic_mind.py` | If present locally |
| `platform/adapters/dispatch.py` | If present locally |
| `schemas/synthetic_mind_bundle.v1.json` | If present locally |
| `.github/workflows/synthetic-mind-bundle-gate.yml` | If present locally |
| `tests/test_synthetic_mind_*.py` | Bundle tests |

Verify: `make synthetic-mind-gate`

## PR-C — Lab, Mechanic, Slingshot, frontend panels

| Path | Notes |
|------|-------|
| `lab/replay.py`, `lab/routes.py` | If present locally |
| `.mechanic/`, `mechanic/fixtures/sample-customer-repo-clean/` | Dogfood |
| `mechanic/genome/adapters/governance_manifest.py` | If present locally |
| `frontend/src/components/CoherenceProjectionPanel.*` | If present locally |
| `frontend/src/components/JarvisSlingshotPanel.*` | If present locally |
| `slingshot/**` | If modified |

Verify: `make lab-gate`, `make mechanic-gate`, `make slingshot-gate`

## PR-D — Docs, proof bundles, trust bundles

| Path | Notes |
|------|-------|
| `docs/audit/REPO_HYGIENE_MANIFEST.json` | Steward manifest |
| `docs/proof/repo/REPO_STEWARD_V1_PROOF_BUNDLE.md` | Steward proof |
| `docs/proof/**` | Production hardening, lab, narrative, slingshot |
| `docs/trust_bundles/2026-06-02-*.md` | If present locally |
| `docs/operations/PRODUCTION_RELEASE_WORKFLOW.md` | If present locally |
| `document/governance/CANONICAL_RUNTIME_LANE.md` | Canonical lane |
| `document/compliance/BLUEPRINT_DELTA_CHECKLIST.md` | Blocker #1 closed |
| `docs/runtime/SYNTHETIC_MIND.md` | Lane promotion section |
| `docs/audit/LOGBOOK.md` | Purge entry |

Verify: `python3 .github/scripts/validate-documentation-baseline.py`

## Exclude from all PRs

Root ISOs, PDFs, duplicate import trees, whitespace poison dir, `start_jarvis.py` sidecar at repo root.
