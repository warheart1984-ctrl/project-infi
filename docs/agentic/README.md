# Agentic coding agent — Project Infinity 1 template

Project-Infinity1 uses **[agentic-coding-agent](https://github.com/warheart1984-ctrl/agentic-coding-agent)** as the structural template for lawful, receipt-backed coding agents.

## Layout

```
Project-Infinity1/
├── AGENTS.md                    ← Cursor / Nova session rules (this template)
├── nova-mission-002/            ← Mirrored Mission #002 (CRK-2 + Agent SDK + Cockpit)
├── lawful-nova-shell/           ← Lawful Nova CLI + dev shell
├── src/crk1/                    ← CRK-1 Python runtime (missions 005–006, CAA-1)
├── sdk/continuity-sdk/          ← CDP-1 / CEP experiment harness
└── scripts/
    ├── start-agentic-coding-stack.ps1
    ├── start-nova-stack.ps1
    ├── restart-aais.ps1
    └── verify-nova-local.ps1
```

## Quick start (agentic + lawful local LLM)

### 1. Mission #002 TypeScript agent

```powershell
cd nova-mission-002
npm install
npm run build
npm test
```

See `nova-mission-002/MISSION-002.md` and `nova-mission-002/observer/REPRO_PROTOCOL.md`.

### 2. Full local stack (Windows)

```powershell
# From repo root
.\scripts\start-agentic-coding-stack.ps1
.\scripts\verify-nova-local.ps1
```

### 3. AAIS on-device inference only

```powershell
.\scripts\restart-aais.ps1 -LocalReal
# POST http://127.0.0.1:8000/legacy_api/api/text/generate
```

`-LocalReal` sets:

- `--preset laptop` → `Qwen/Qwen2.5-0.5B-Instruct` (int4, local HF)
- `AAIS_FORCE_LOCAL_MODEL=1` → skip API-backed mock path
- `CONSTITUTIONAL_BOOT_SKIP=1` → dev escape hatch if CSR disk hydration fails

**Production:** fix or clear invalid persisted CSR state under `.runtime/` instead of leaving skip enabled.

## Re-sync from upstream

```powershell
# Edit canonical repo first: E:\agentic-coding-agent
robocopy E:\agentic-coding-agent nova-mission-002 /E /XD shell .git node_modules dist /XF RELEASE.md
```

Details: `nova-mission-002/SYNC.md`.

## What each layer proves

| Layer | Proves |
|-------|--------|
| `nova-mission-002` | External observer can run CRK-2 governed agent + cockpit |
| `lawful-nova-shell` | Local Nova CLI, LSG, frontier chat |
| `src/crk1` + continuity SDK | CRK-1 receipts, assimilation (CAA-1), CDP-1 experiments |
| AAIS `laptop` + force local | Real torch weights on laptop CPU/GPU |

## Cursor

Open the repo root. Cursor reads **`AGENTS.md`** at the repository root automatically.
