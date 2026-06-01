# AAIS Frontend

Modern React-based web UI for the AAIS multi-modal AI system.

## Installation

```bash
cd frontend
npm install
```

## Development

```bash
npm start
```

The app will open at `http://localhost:3000`

`npm start` runs the Vite development server on port `3000`.

## Build

```bash
npm run build
```

The production build is written to `build/` so the existing Docker and CI flow
can keep serving the same artifact path.

For the packaged AAIS app, use the repo-root launcher instead of invoking Vite
manually:

```bash
python -m aais prepare --force-build --data-dir ./.runtime/aais-data
```

That command builds the frontend with the packaged `/app` base path and stages
the release bundle into `app/static/` for the FastAPI shell.

## Test

```bash
npm run test:ci
```

For coverage in CI-compatible mode:

```bash
npm test -- --coverage --watchAll=false
```

## Workflow Smoke

```bash
npm run smoke:workflow
```

This starts an isolated FastAPI + Celery + Vite stack, drives the workflow shell
through onboarding, templates, builder, runs, and approvals in a real browser,
and cleans up after itself unless `KEEP_WORKFLOW_SMOKE_ARTIFACTS=1` is set.

Workflow/onboarding classification:

- `/workflows/*` and `/onboarding` are live canonical workflow-shell routes
- they are owned by `app/main.py` and the workflow frontend pages
- they are not reference-only pages
- `src/api.py` still owns core Jarvis operator semantics and canonical Jarvis runtime truth

## External Suggestion Admission

This frontend inherits the project-wide external suggestion admission law.

Outside proposals may be rendered, compared, critiqued, summarized, or used as
reference in UI work, but the UI must not present them as adopted AAIS truth
unless project law has already admitted the documented form.

## Features

- **Dashboard** - Overview of all features
- **Text Generator** - Generate uncensored text
- **Image Analyzer** - Analyze images
- **Image Generator** - Create images from text
- **Audio Processor** - Process audio files
- **Batch Processor** - Process multiple items
- **History** - View generation history
- **Settings** - Configure preferences

## API Integration

The frontend connects to the backend API at `http://localhost:8000`

To override that, set `VITE_API_URL` before starting the frontend. The legacy
`REACT_APP_API_URL` name is still accepted for compatibility.

Legacy `/api/*` requests are forwarded through the FastAPI runtime via its
mounted compatibility surface, so the frontend can rely on one backend host and
port during the transition away from the older Flask API.

Make sure the backend is running before starting the frontend.
