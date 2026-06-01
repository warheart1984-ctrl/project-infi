# UGR Governed Ingestion Contract (UGR-IC-01)

Status: **Phase 3 admitted** — curated senses without model I/O.

Authority: `docs/contracts/UGR_RUNTIME_CONTRACT.md`, `docs/programs/UGR_CLOUD_PROGRAM.md`.

## Core Law

1. **No raw internet to models** — ingestion fetch/normalize/extract runs outside LLM lanes.
2. **Curated sources only** — sources must be declared in `deploy/ugr/ingestion.sources.json`.
3. **Sanitize first** — PII patterns and secret-like strings are redacted or blocked.
4. **Invariant gate before ledger** — proposals fail closed on structural/policy violations.
5. **Provenance required** — every accepted claim links to evidence + source URI.

## Pipeline Stages

```text
fetch → sanitize → normalize → extract → invariant gate → ledger proposal
```

Implementation: `src/ugr/ingestion/pipeline.py`

## Supported Source Types (v0)

| Type | Purpose |
|---|---|
| `arxiv` | Atom feed queries (research) |
| `github_releases` | Release metadata for a repo |
| `rss` | Operator-configured RSS/Atom feeds |

## API

### Monolith / AAIS API

- `GET /api/ugr/ingest/sources`
- `POST /api/ugr/ingest` — body: `{ "source_id": "...", "dry_run": false }`

### Mesh service (`ingestion` :8095)

- `GET /v1/ingestion/sources`
- `POST /v1/ingestion/run`
- `POST /v1/ingestion/run-enabled`

## Configuration

Path: `deploy/ugr/ingestion.sources.json`  
Override: `UGR_INGESTION_CONFIG`

## Verification

```bash
make ugr-ingestion-gate
py -3.12 -m pytest tests/test_ugr_ingestion.py -q
```
