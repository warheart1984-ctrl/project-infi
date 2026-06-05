# How to Use AAIS (Human Guide)

Simple steps to install, configure, and run AAIS on your machine.

**Also see:** [AAIS Operator Guide](AAIS_OPERATOR_GUIDE.md) (desktop builds) · [First-Time Operator Guide](../operations/FIRST_TIME_OPERATOR_GUIDE.md) (tiered onboarding)

---

## 1. What you need

| Item | Required? | Notes |
|------|-----------|-------|
| Python 3.10+ | Yes | `python --version` |
| Git | Yes | To clone the repo |
| Node.js 18+ | Optional | Only to rebuild the frontend or run frontend tests |
| Redis | Optional | For background Celery jobs |
| API keys | Optional | Mock mode works without any keys |

---

## 2. Install

```bash
git clone https://github.com/warheart1984-ctrl/Project-Infinity1.git
cd Project-Infinity1
python -m pip install -e ".[dev]"
cp .env.example .env
```

Never commit `.env`. It holds your secrets.

---

## 3. Start AAIS

```bash
python -m aais prepare --data-dir ./.runtime/aais-data
python -m aais doctor --data-dir ./.runtime/aais-data
python -m aais start --data-dir ./.runtime/aais-data --preset mock --no-browser
```

| Command | What it does |
|---------|--------------|
| `prepare` | Stages the web UI into `app/static/` |
| `doctor` | Prints a health summary (paths, bundle ready, etc.) |
| `start` | Runs the server on `http://127.0.0.1:8000` |

**Without API keys:** use `--preset mock`.

**With real providers:** use `--preset default` after adding keys to `.env`.

**Open the app:** http://127.0.0.1:8000/app

---

## 4. Environment variables

Copy `.env.example` to `.env` and set only what you use.

### Runtime basics

| Variable | Purpose |
|----------|---------|
| `ENVIRONMENT` | `development` (default) or `production` |
| `JARVIS_DATA_DIR` | Where AAIS stores local data (launcher sets this with `--data-dir`) |
| `AAIS_PRESET` | `mock`, `laptop`, or `default` |
| `AAIS_OTEM_CAPABILITY_LEVEL` | OTEM ceiling (default `10`) |

### Constitutional substrate (production)

These flags make AAIS **fail closed** when governance files are missing:

| Variable | When set to `1` |
|----------|-----------------|
| `AAIS_REQUIRE_CONSTITUTIONAL_LAW` | Refuses start if `lawbook/META_ARCHITECT_LAWBOOK.md` is missing |
| `AAIS_REQUIRE_COLLABORATION_CHARTER` | Refuses chat turns if `lawbook/HUMAN_AI_CO_COLLABORATION_CHARTER.md` is missing |

**Production default:** when `ENVIRONMENT=production`, both flags default to `1` if you leave them unset.

**Development:** leave them unset (or set `0`) for graceful degrade when lawbook/charter are absent.

Tracked copies live under `lawbook/`. See [Constitutional Layer](../substrate/CONSTITUTIONAL_LAYER.md).

### Provider keys (optional)

| Provider | Set in `.env` |
|----------|---------------|
| OpenAI | `OPENAI_API_KEY` |
| Anthropic (Claude) | `ANTHROPIC_API_KEY` |
| OpenRouter | `OPENROUTER_API_KEY` |
| Google (Gemini) | `GOOGLE_API_KEY` |
| NVIDIA Nemotron | `NVIDIA_API_KEY` |

Full list: [`.env.example`](../../.env.example) and [Frontier Model Adapters](../providers/FRONTIER_MODEL_ADAPTERS.md).

### Auth / session (production)

| Variable | Purpose |
|----------|---------|
| `SECRET_KEY` | Flask session signing — use a long random string |
| `JWT_SECRET` | JWT signing for operator auth |
| `APP_BEARER_TOKEN` | Optional bearer token for API access |
| `AUTH_REQUIRED` | Set `1` to require auth on protected routes |

Generate strong secrets locally. Never commit them.

---

## 5. Putting keys in safely

### OpenRouter

1. Create a key at [openrouter.ai](https://openrouter.ai/).
2. Add to `.env`:
   ```env
   OPENROUTER_API_KEY=sk-or-v1-...
   AAIS_OPENROUTER_MODEL=openrouter/free
   ```
3. Restart AAIS.
4. Verify: `GET http://127.0.0.1:8000/legacy_api/api/jarvis/providers` — `openrouter` shows `available: true`.

**Windows helper:** `tools/ops/rotate-openrouter-key.ps1 -VerifyOnly` checks that no live key is committed.

### JWT / session

```env
SECRET_KEY=<long-random-string>
JWT_SECRET=<another-long-random-string>
```

Rotate these when promoting to production. Do not use the template defaults.

---

## 6. Verify everything works

```bash
# Health
curl -fsS http://127.0.0.1:8000/health

# Doctor summary
python -m aais doctor --data-dir ./.runtime/aais-data

# Governance gates (quick)
make naming-gate constitutional-substrate-gate

# UL smoke
python -m tools.ul.smoke
```

A healthy chat turn returns `ul_substrate`, `law_enforcement`, and `cisiv_stage` on the API payload.

---

## 7. Constitutional substrate — what it means for you

AAIS ships a **constitutional layer** that sits above normal code:

- **Lawbook** (`lawbook/META_ARCHITECT_LAWBOOK.md`) — supreme governance rules
- **Charter** (`lawbook/HUMAN_AI_CO_COLLABORATION_CHARTER.md`) — human–AI collaboration rules
- **Engines** — `src/substrate/meta_law_engine.py` and `src/substrate/ingress/collaboration_membrane.py`

In production (`ENVIRONMENT=production`), AAIS refuses to run without these files present. In development, missing files degrade gracefully so you can iterate.

---

## 8. Troubleshooting

| Problem | Fix |
|---------|-----|
| `prepare` says frontend missing | Run `npm install` and `npm run build` in `frontend/`, or use the prebuilt `app/static/` bundle |
| Port 8000 in use | `python -m aais start --port 8001 ...` |
| Provider shows unavailable | Check `.env` key name, restart AAIS, verify with `/jarvis/providers` |
| Constitutional start refused | Ensure `lawbook/` files exist, or use `ENVIRONMENT=development` locally |
| OpenRouter errors | Confirm key in `.env` only (not committed); run rotate script `-VerifyOnly` |
| Redis connection errors | Start Redis locally or remove Celery-dependent workflows |

---

## 9. Next steps

- [AAIS Operator Guide](AAIS_OPERATOR_GUIDE.md) — desktop EXE, offline use
- [First-Time Operator Guide](../operations/FIRST_TIME_OPERATOR_GUIDE.md) — Docker pilot, advanced tiers
- [CHANGELOG](../../CHANGELOG.md) — release history
