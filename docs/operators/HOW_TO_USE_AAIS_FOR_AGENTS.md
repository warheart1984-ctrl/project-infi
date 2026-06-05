# How to Use AAIS (AI Agent Guide)

Machine-oriented reference for agents operating on the AAIS repository.

**Human-readable version:** [HOW_TO_USE_AAIS.md](HOW_TO_USE_AAIS.md)

---

## 1. Bootstrap sequence

```bash
git clone https://github.com/warheart1984-ctrl/Project-Infinity1.git
cd Project-Infinity1
python -m pip install -e ".[dev]"
cp .env.example .env
python -m aais prepare --data-dir ./.runtime/aais-data
python -m aais doctor --data-dir ./.runtime/aais-data
python -m aais start --data-dir ./.runtime/aais-data --preset mock --no-browser
```

Exit codes: `0` = success; non-zero = failure. Do not proceed past a failed gate.

---

## 2. Canonical commands

| Action | Command | Expected exit |
|--------|---------|---------------|
| Start (mock) | `python -m aais start --data-dir ./.runtime/aais-data --preset mock --no-browser` | blocks (server) |
| Health | `curl -fsS http://127.0.0.1:8000/health` | 0 |
| Full pytest | `AAIS_GENOME_BOOT=warn python -m pytest -q` | 0 |
| Naming gate | `python tools/naming_protocol_lint.py` | 0 |
| Constitutional gate | `make constitutional-substrate-gate` | 0 |
| UL smoke | `python -m tools.ul.smoke` | 0 |
| Cross-machine matrix | `python tools/proof/run_flagship_cross_machine_matrix.py --role primary` then `--role secondary` then `--compare` | 0 each |
| Frontend CI | `cd frontend && npm run test:ci && npm run build && npm run audit:prod` | 0 |
| Mobile CI | `cd mobile && npm run typecheck && npm audit --omit=dev` | 0 |

---

## 3. Environment variables (agent-critical)

| Name | Values | Effect |
|------|--------|--------|
| `ENVIRONMENT` | `development` / `production` | Production arms constitutional fail-closed defaults |
| `AAIS_REQUIRE_CONSTITUTIONAL_LAW` | `1` / `0` / unset | `1` → refuse start if lawbook missing |
| `AAIS_REQUIRE_COLLABORATION_CHARTER` | `1` / `0` / unset | `1` → refuse turn if charter missing |
| `AAIS_GENOME_BOOT` | `warn` | Suppress genome boot noise in pytest |
| `JARVIS_DATA_DIR` | path | Runtime data root |
| `OPENROUTER_API_KEY` | `sk-or-...` | Enables OpenRouter provider |
| `SECRET_KEY` | string | Session signing |
| `JWT_SECRET` | string | JWT signing |

**Production auto-defaults** (when `ENVIRONMENT=production` and flag unset):

- `AAIS_REQUIRE_CONSTITUTIONAL_LAW=1`
- `AAIS_REQUIRE_COLLABORATION_CHARTER=1`

Wired in: `app/config.py`, `aais/launcher.py`, `api/index.py`.

---

## 4. Constitutional substrate paths

| Artifact | Path |
|----------|------|
| Lawbook (tracked) | `lawbook/META_ARCHITECT_LAWBOOK.md` |
| Charter (tracked) | `lawbook/HUMAN_AI_CO_COLLABORATION_CHARTER.md` |
| Meta law engine | `src/substrate/meta_law_engine.py` |
| Collaboration membrane | `src/substrate/ingress/collaboration_membrane.py` |
| Bootstrap hooks | `tests/governance_bootstrap.py` |
| Tests | `tests/test_constitutional_substrate.py` |
| Spec | `docs/substrate/CONSTITUTIONAL_LAYER.md`, `docs/substrate/INGRESS_COLLABORATION_MEMBRANE.md` |

Admission bootstrap:

```python
from tests.governance_bootstrap import ensure_constitutional_substrate, ensure_collaboration_charter_ready
ensure_constitutional_substrate()
ensure_collaboration_charter_ready()
```

---

## 5. Makefile gate targets (subset)

```bash
make naming-gate
make naming-genome-gate
make meta-linguistic-gate
make constitutional-substrate-gate   # meta-law-gate + collaboration-charter-gate
make alt30-governed-gate
make v1.26.1-gate
```

---

## 6. Claim labels and proof obligations

Per `REPO_PROOF_LAW.md` and Meta Architect Lawbook:

| Label | Meaning |
|-------|---------|
| `proven` | Reproducible evidence exists (log, test, matrix artifact) |
| `asserted` | Claim stated; evidence incomplete |
| `rejected` | Claim disproven or blocked |

Trust bundle template: `docs/trust_bundles/*.md`

Required fields: `claim_label`, `proof_links`, `why_short`, `created_at_utc`.

Cross-machine proof: `docs/proof/aais-ul/FLAGSHIP_CROSS_MACHINE_MATRIX.md`  
Matrix tool: `tools/proof/run_flagship_cross_machine_matrix.py`  
Artifacts: `.runtime/cross_machine_matrix/`

---

## 7. What agents MUST NOT do

1. **Commit secrets** — never add `.env`, live API keys, or `sk-or-` strings to git.
2. **Bypass gates** — do not skip `naming-gate`, `constitutional-substrate-gate`, or pytest before ship claims.
3. **Force-push main/master** — forbidden unless operator explicitly requests.
4. **Edit plan files** — do not modify operator plan artifacts unless asked.
5. **Claim flagship GA** without trust-bundle reconciliation and cross-host evidence.
6. **Set `claim_label: proven`** without linked reproducible artifacts.

---

## 8. OpenRouter key hygiene

```powershell
tools/ops/rotate-openrouter-key.ps1 -VerifyOnly
```

Confirms no live key in `.env`/environment before audit. Apply new keys only via local `.env` edit — never commit.

---

## 9. Frontend / mobile verification

```bash
cd frontend
npm run test:ci      # exit 0
npm run build        # exit 0
npm run audit:prod   # exit 0, 0 prod vulns

cd ../mobile
npm run typecheck    # exit 0
npm audit --omit=dev # exit 0, 0 prod vulns
```

Archive logs to `.runtime/pilot-ga-frontend-*.log`, `.runtime/pilot-ga-mobile-*.log`.

---

## 10. Admission tokens and cold start

Governance test harness uses `tests/governance_bootstrap.py` for cold-start admission. Pytest entry may call `ensure_constitutional_substrate()` before substrate-sensitive tests.

For API turns, collaboration membrane evaluates `claim_label` on trace payloads — invalid labels block admission when charter is required.

---

## 11. Release checklist (agent)

1. Run gates + pytest (single host minimum).
2. Run cross-machine matrix (`primary` → `secondary` → `compare`).
3. Run frontend/mobile audit:prod.
4. Update `CHANGELOG.md` and trust bundle.
5. Create annotated tag: `git tag -a vX.Y.Z -m "..."`.
6. Push branch and tag (only when operator requests).
7. Document proven vs asserted in trust bundle — do not inflate scores.
