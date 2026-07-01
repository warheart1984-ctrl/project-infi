# Developer Onboarding - Nova Continuity Substrate

Welcome to the Nova substrate project.

This guide helps you get productive quickly.

## 1. What You Are Building

You are not building Nova OS.

You are building the minimal continuity substrate:

- Events
- Timeline
- Lineage
- Receipts
- File continuity

Everything else lives in FUTURE.md.

## 2. Setup

Backend / runtime:

```bash
pip install -e ".[dev]"
python -m aais start
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

## 3. Code Structure

app/

- main.py - FastAPI workflow shell and app host

src/

- api.py - Jarvis runtime API surface

frontend/

- src/pages/ - React/Vite pages
- src/components/ - UI components

## 4. Development Rules

1. Do not add features beyond v0.2.
2. Do not implement governance, agents, CKCE-1, or wave signatures.
3. All future ideas go into FUTURE.md.
4. All work must satisfy acceptance tests.
5. Keep PRs small and scoped.

## 5. How to Contribute

1. Pick one milestone from MILESTONES.md.
2. Make the smallest implementation that satisfies the matching acceptance tests.
3. Keep future architecture out of substrate code.
4. Update docs only when behavior changes.
5. Open a focused review.

## 6. When the Substrate Is Proven

After v0.0, v0.1, and v0.2 pass:

- Lock the substrate.
- Review FUTURE.md.
- Pull only the next proven layer into scope.

Until then: substrate only.
