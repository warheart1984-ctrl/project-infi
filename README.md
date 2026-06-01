# Project Infinity — AAIS

> **Adaptive Authority Intelligence System (AAIS)** — a law-governed Jarvis runtime with inspectable Universal Language (UL) structure, Project Infi admission, and operator-facing surfaces.

## What AAIS Is

AAIS is not a single chatbot wrapper. It is a **governed cognition runtime** that:

- routes operator turns through **Jarvis** (`src/api.py`, `src/jarvis_operator.py`)
- adapts every outward payload through **AAIS-UL** (structure + visibility before expansion)
- enforces **Project Infi law** on chat replies, forge contractors, and repo mutations
- stages work on the **CISIV** ladder: concept → identity → structure → implementation → verification
- exposes traces, law enforcement, and UL substrate envelopes on live API responses

Think of it in three cooperating layers:

| Layer | Role | Key modules |
|---|---|---|
| **Authority shell** | Sessions, chat, tools, forge handoffs, operator UI | `src/api.py`, `app/main.py`, `aais/launcher.py` |
| **UL substrate** | Payload adaptation, modular previews, drift/smoke tooling | `src/aais_ul.py`, `src/chat_turn_governance.py`, `src/forge_repo_governance.py` |
| **Governed law** | Admission, repo change cycles, module governance | `src/project_infi_law.py`, `src/project_infi_state_machine.py` |

Authoritative references:

- Subsystem map: [`docs/runtime/AAIS_SUBSYSTEM_SPEC.md`](docs/runtime/AAIS_SUBSYSTEM_SPEC.md)
- UL doctrine: [`docs/contracts/AAIS_UL_DOCTRINE.md`](docs/contracts/AAIS_UL_DOCTRINE.md)
- Latest UL/CISIV proof: [`docs/proof/aais-ul/UL_CISIV_PHASES_1_5_PROOF.md`](docs/proof/aais-ul/UL_CISIV_PHASES_1_5_PROOF.md)

This repository is also **Project Infi** — constitutional engineering where claims require proof, not intent.

---

## How to Make It Work

### Prerequisites

- **Python 3.10+**
- **Git**
- **Node.js 18+** and **npm** — only if you need to rebuild the frontend (`frontend/`)
- Optional: **Redis** — for Celery background jobs (`make worker`)
- Optional: provider API keys — OpenAI / Anthropic (local/mock presets work without them)

### 1. Clone and install

```bash
git clone https://github.com/warheart1984-ctrl/Project-Infinity1.git
cd Project-Infinity1
python -m pip install -e ".[dev]"
```

Copy environment template and set keys only for routes you use:

```bash
cp .env.example .env
# Edit .env — OPENAI_API_KEY / ANTHROPIC_API_KEY optional for mock or laptop presets
```

### 2. Prepare runtime data (first run)

```bash
python -m aais prepare --data-dir ./.runtime/aais-data
python -m aais doctor --data-dir ./.runtime/aais-data
```

`prepare` stages the packaged UI into `app/static/`. A prebuilt bundle ships with the repo; use `--force-build` only after `npm install` in `frontend/`.

### 3. Start AAIS

**Recommended (cross-platform launcher):**

```bash
python -m aais start --data-dir ./.runtime/aais-data --preset mock --no-browser
```

Presets (`src/main.py`):

| Preset | Use when |
|---|---|
| `mock` | No GPU / no API keys — deterministic local replies |
| `laptop` | Lightweight real local model path |
| `default` | Full runtime (may load heavier local models) |

**Developer alternative (uvicorn directly):**

```bash
make run
# equivalent: uvicorn app.main:app --reload
```

### 4. Open operator surfaces

| Surface | URL |
|---|---|
| Health | http://127.0.0.1:8000/health |
| App shell | http://127.0.0.1:8000/app |
| Jarvis console | http://127.0.0.1:8000/app/jarvis |
| Legacy Jarvis API (Flask) | mounted at `/legacy_api` via FastAPI bridge |

### 5. Verify it is working

```bash
curl -fsS http://127.0.0.1:8000/health
```

Create a chat session and send a message:

```bash
curl -fsS -X POST http://127.0.0.1:8000/legacy_api/api/chat/sessions \
  -H "Content-Type: application/json" \
  -d "{\"system_prompt\":\"You are Jarvis.\"}"

# Use session_id from response:
curl -fsS -X POST http://127.0.0.1:8000/legacy_api/api/chat/sessions/<session_id>/message \
  -H "Content-Type: application/json" \
  -d "{\"message\":\"Summarize AAIS.\",\"response_mode\":\"operator\"}"
```

A healthy turn returns `ul_substrate`, `modular_preview`, `law_enforcement`, and `cisiv_stage` on the payload.

**UL governance smoke:**

```bash
python -m tools.ul.drift
python -m tools.ul.smoke
python -m pytest tests/test_cisiv.py tests/test_chat_turn_governance.py tests/test_forge_repo_governance.py -q
```

### 6. Optional contractor lanes

These are isolated HTTP services — start only when you need forge/evolve features:

| Service | Default port | Env var |
|---|---|---|
| Forge contractor | 6060 | `FORGE_BASE_URL` |
| ForgeEval | 6061 | `FORGE_EVAL_BASE_URL` |
| EvolveEngine | 6062 | `EVOLVE_BASE_URL` |

Without them, core chat and patch-review paths still work; explicit forge routes return routing errors until the contractor is up.

---

## GitHub

| Item | Location |
|---|---|
| Repository | https://github.com/warheart1984-ctrl/Project-Infinity1 |
| Contributing | [`CONTRIBUTING.md`](CONTRIBUTING.md) |
| CI workflows | [`.github/workflows/`](.github/workflows/) |
| Local-only rules | [`.gitignore`](.gitignore), [`docs/GITHUB.md`](docs/GITHUB.md) |

Pull requests to `main` run governance gates (CoGOS CI, documentation baseline, UGR trust bundle, operator console, Forgekeeper, Scorpion). Significant claims in PRs must include proof posture (`asserted` / `proven` / `rejected`) per [`REPO_PROOF_LAW.md`](REPO_PROOF_LAW.md).

**Do not commit:** ISO images, `.runtime/`, `wolf-cog-os/output/`, or duplicate import folders (`*-main/`).

### Failsafe notes

- Stop foreground runtime with `Ctrl+C`.
- Do not delete `.runtime/aais-data` during active sessions.
- Missing proof or constitutional ambiguity is a **stop condition** — see governance section below.

---

## Repository Layout (operator view)

```
aais/              Cross-platform launcher (start | prepare | doctor)
app/               FastAPI workflow shell + packaged static UI
src/               Jarvis runtime authority (api, operator, UL, law)
frontend/          React operator UI source (build → app/static)
forge/             Isolated Forge contractor service
tools/ul/          UL drift + smoke verification
docs/              Contracts, subsystem spec, proof packets
tests/             Pytest suite
```

---

## Constitutional Governance

Behavior is constitutional, not aspirational. No fix, test, or release claim is complete without evidence.

**Precedence:** Law > Blueprint > Contract > Implementation > Pipeline > Tool

Governance references:

- [`META_ARCHITECT_LAWBOOK.md`](META_ARCHITECT_LAWBOOK.md)
- [`REPO_PROOF_LAW.md`](REPO_PROOF_LAW.md)
- [`HUMAN_AI_CO_COLLABORATION_CHARTER.md`](HUMAN_AI_CO_COLLABORATION_CHARTER.md)
- [`docs/TRUST_BUNDLE_SPEC.md`](docs/TRUST_BUNDLE_SPEC.md)

| Role | Responsibility |
|---|---|
| **Human** | Define law, approve exceptions, review evidence, hold release authority |
| **AI / agents** | Execute within law, emit traceable evidence, label claims (`asserted`, `proven`, `rejected`) |

### Doctrine summary (twelve doctrines)

| # | Doctrine | Intent |
|---|---|---|
| I | Proof-of-Reality | If it was not proven, it did not occur. |
| II | Blueprint | Intent documented before or with implementation change. |
| III | Documentation | Operation without current docs is non-compliant. |
| IV | Failsafe | Safe defaults, rollback, recovery, stop conditions. |
| V | Evidence | Claims require traceable proof artifacts. |
| VI | Debt | Gaps tracked with owner, severity, due date, status. |
| VII | CI Governance | Governance gates are mandatory acceptance controls. |
| VIII | Precedence | Higher-order artifacts govern conflicts. |
| IX | Change-of-Reality | Behavior changes require doc + test + proof updates. |
| X | Meta Architect Authority | Final constitutional interpretation is binding. |
| XI | Simple Trust | Evidence-first; trust bundles; human escalation when needed. |
| XII (MA-12) | Operational Primer | README must include **How to Make It Work** (this section). |

Templates: [`templates/PROOF_BUNDLE_TEMPLATE.md`](templates/PROOF_BUNDLE_TEMPLATE.md), [`templates/PROJECT_BASELINE_CHECKLIST.md`](templates/PROJECT_BASELINE_CHECKLIST.md)

---

## Contributor Oath

1. I will not present unproven claims as complete.
2. I will attach traceable evidence to significant fix/test/release claims.
3. I will preserve constitutional precedence and no-bypass governance.
4. I will track documentation/governance debt instead of hiding it.
5. I will treat missing evidence as a stop condition, not a paperwork delay.

---

## Contributors

See [`CONTRIBUTORS.md`](CONTRIBUTORS.md).

- **Jon Halstead** — maintainer and constitutional authority
- **Cursor Agent (Auto)** — AI implementation collaborator (UL/CISIV Phases 1–5, governance modules, proof bundles, operational README; commits `7b4e806`, `b086b1e`)

Human–AI collaboration follows [`HUMAN_AI_CO_COLLABORATION_CHARTER.md`](HUMAN_AI_CO_COLLABORATION_CHARTER.md).
