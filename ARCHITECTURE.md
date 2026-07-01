# Project-Infi Architecture

One-page map of what lives in this repo, who owns it, and where new code belongs.

**Detailed docs:** [docs/README.md](docs/README.md) (spine → runtime → contracts).

---

## Three product tracks

| Track | Purpose | Canonical paths | Entry |
|-------|---------|-----------------|-------|
| **AAIS / Jarvis** | Cognition runtime + workflow shell | `aais/` → `app/` + `src/` + `frontend/` | `python -m aais start` → `:8000` |
| **Lawful Nova / Operator** | Governed agent loop + lawful LLM API | `nova/` + `operator_kernel/` + `lawful-nova-shell/` | `:8080`, `:8790`, `:8791` |
| **AAES-OS spine** | UCR trace / governed-memory (TypeScript) | `aaes-os/` (+ Python facade `runtime_law_spine/`) | `cd aaes-os && pnpm build` |

All three share **constitutional law** (`constitutional/`) and the **subsystem genome registry** (`governance/subsystem_genomes/`).

---

## Authority table (one owner per concern)

| Concern | Owner | Do not duplicate in |
|---------|-------|---------------------|
| Jarvis cognition / chat API | `src/api.py` (runtime truth) | `app/`, scripts |
| Workflow shell, static UI host | `app/main.py` | `src/` routes |
| Launcher / doctor | `aais/launcher.py` | — |
| Constitutional articles, ECK, JPSS | `constitutional/` | `constitutional_state/` shims (legacy) |
| Operator agent loop, patches | `operator_kernel/` | `src/` operator copies |
| Lawful LLM + continuity | `nova/` | `lawful-nova-shell/nova/` (distribute only; parent is canonical) |
| Forge / evolve contractors | `forge/`, `tools/services/start_*.py` | `src/` |
| Platform ops membrane | `platform/` | cognition core |
| CoG OS ISO forge | `cog-os/` | — |
| Active engineering docs | `docs/` | `document/` (index only; merge over time) |
| Closed-wave / historical | `archive/`, `docs/_archive/`, `docs/_future/` | live runtime |

---

## Dependency direction

```
aais (launcher)
  → app (FastAPI shell)
  → src (cognition)
operator_kernel / nova
  → constitutional (law)
contractors (forge, platform, …)
  → HTTP boundary only — no src/* imports
```

`constitutional/` must not import `operator_kernel/`. Tests under `tests/constitutional/` should not depend on operator orchestration.

---

## Purpose test (keep, fix, or archive)

For any file or directory:

1. **Which track owns it?** If unclear → document or move.
2. **Live or ceremonial?** Runtime import / CI gate vs one-shot bootstrap → archive ceremony.
3. **Single authority?** Duplicate tree (Py+TS mirror, second Nova copy) → delegate or pick one canonical path.
4. **Succession of judgment?** Receipts, continuity, gates → keep. Alt-wave promotion only → archive.

If (1) unclear, (2) ceremonial, (3) duplicated, (4) no → **archive or delete**.

---

## Where to put new code

| You are building… | Put it in… |
|-------------------|------------|
| Jarvis behavior, providers, memory | `src/` (prefer new modules; avoid growing `api.py`) |
| HTTP workflow, OTEM, Celery tasks | `app/` |
| Constitutional article, register, gate | `constitutional/<domain>/` + `tests/constitutional/` |
| Operator tool, patch flow, CSR wiring | `operator_kernel/` |
| Nova API, lawful inference | `nova/` |
| Isolated mutation / eval service | New contractor package + `docs/contracts/` |
| Subsystem with genome | Runtime + contract + Makefile gate, then genome JSON |
| Experiment / closed wave | `archive/` or `docs/_future/` — not root |

---

## Live spine (mental model)

```
aais → app + src
        ↓
   constitutional ← operator_kernel + nova
        ↓
   governance (genomes, proof) + docs/contracts
```

Contractors and `cog-os/` attach at the edges. `aaes-os/` is a sibling spine for UCR TypeScript, not a replacement for `src/`.

---

## Cleanup status

- **Phase 1 (done):** dead file removal, alt bootstrap archive, doc path fixes, this file, `constitutional*` in `pyproject.toml`.
- **Phase 2+:** finish `scripts/substrate_collapse_migrate.py`, unify succession gates, decompose `src/api.py` — see audit notes in repo history.
