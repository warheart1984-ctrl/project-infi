# Nova Operator Cockpit

Constitutional operator HUD for Nova × CRK‑1.

## Run

```bash
# From repo root — build SDK first
cd ..
npm run build

cd cockpit
npm install
npm run dev
```

Open http://localhost:5173

## Architecture

- **NovaShell** — cockpit grid (top bar, rails, canvas, bottom band)
- **Zustand store** — unified cockpit state
- **NovaEventBridge** — SDK events → store (plan, action, receipt, violation, heartbeat)
- **Panels** — Plan, Diff, Receipts, Continuity, Invariants, Kernel + Agent Console

## Design tokens

See `src/styles/tokens.json` and `src/styles/variables.css`.
