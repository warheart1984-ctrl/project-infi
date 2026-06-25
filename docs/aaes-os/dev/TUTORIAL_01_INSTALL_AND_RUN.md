# Tutorial 1 — Install and Run the Spine

## Prerequisites

- Node.js ≥ 20
- pnpm ≥ 9
- Python 3.11+ (for CRK-1 / CDP-1 at repo root)

## Install

```bash
git clone https://github.com/warheart1984-ctrl/Project-Infinity1.git
cd Project-Infinity1
pip install -e .

cd aaes-os
pnpm install
pnpm build
```

## Run the AAES-OS spine

```bash
pnpm test
```

Expected: workspace packages build and vitest integration tests pass.

## Run CRK-1 tests

From repo root:

```bash
pytest tests/crk1 -q
```

## Ops console (optional)

```bash
cd aaes-os
pnpm --filter @aaes-os/ops-console dev
```

- UI: http://localhost:5173
- API: http://localhost:4000/telemetry

## Verify

- `pnpm test` passes in `aaes-os/`
- `pytest tests/crk1` passes at repo root
- Ops console shows telemetry (if started)
