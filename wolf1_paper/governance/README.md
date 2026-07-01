# Governance Dashboard

The AAES-OS Governance Dashboard provides a real-time view of the system's constitutional state. It aggregates governance receipts, requirements, and CTS results into a single static, hostable UI.

## Wireframe

```
┌───────────────────────────────────────────────────────────────┐
│                     AAES-OS Governance Dashboard               │
└───────────────────────────────────────────────────────────────┘

┌───────────────┬────────────────┬──────────────────────────────┐
│ CTS Status     │ Documents Built│ Open ADRs                    │
├───────────────┼────────────────┼──────────────────────────────┤
│     PASS       │       3        │              5               │
└───────────────┴────────────────┴──────────────────────────────┘

Recent Governance Receipts / Active Requirements / Event Feed
```

## Features

- Live governance receipts (version, commit, SHA-256, timestamp)
- Requirements registry viewer
- CTS status indicator
- Document build history
- Governance event feed
- Traceability graph (`graph.html`)
- Dark / light theme toggle

## How it works

The dashboard is powered by generated artifacts:

| File | Purpose |
|------|---------|
| `governance/receipts-index.json` | Aggregated build receipts |
| `governance/governance-status.json` | CTS status, doc count, ADR count |
| `governance/events.json` | Append-only governance activity |
| `registries/requirements.yaml` | Constitutional requirements |

Loaded client-side by `dashboard-loader.js`.

## Updating the dashboard

```bash
make all
```

This triggers CTS validation, document builds, receipt generation, index regeneration, and dashboard artifact refresh.

## Viewing locally

```bash
cd wolf1_paper
npx serve .
# http://localhost:3000/governance/dashboard.html
```

## Static hosting

Works on GitHub Pages, Netlify, Vercel, Cloudflare Pages, or any static host. Publish:

- `governance/`
- `registries/`
- `adr/` (for INDEX links)

## Docs portal

See `docs-portal/governance-dashboard.md` for governance-grade description.
