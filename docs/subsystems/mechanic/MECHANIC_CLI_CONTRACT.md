# AI Mechanic CLI Contract

## Entry

```bash
python -m mechanic --mode <mode> --case-id <id> [options]
```

## Modes

| Mode | Description | Mutates customer repo |
|------|-------------|------------------------|
| `observe` | List adapters and scope | No |
| `scan` | Extract `process_genome.v1` | No |
| `diagnose` | Run invariant evaluators | No |
| `rebuild` | Emit dry-run rebuild bundle | No |
| `report` | Markdown summary from case artifacts | No |
| `extract` | Summarize drift codes | No |
| `status` | Case artifact summary | No |
| `verify` | Proof report + snapshot | No |
| `apply` | **Blocked** — raw apply never enabled | N/A |
| `apply-review` | Create patch review records only (requires `--create-review`) | No |

## Required flags

- `--repo-path` for `scan` and for `diagnose`/`rebuild` when no prior case artifacts exist
- `--write-json` to persist under `.runtime/mechanic/<case-id>/`
- `--trace-path` on `scan` for optional NDJSON trace ingest (or env `MECHANIC_TRACE_PATH`)
- `--create-review` required for `apply-review` (review records only; never writes customer repo)

## Chat enforcement (MECH-CHAT-01)

When `MECHANIC_ENFORCE_PROFILE=1` and `MECHANIC_CASE_ID=<id>`:

- `src/api.py` loads `.runtime/mechanic/<case_id>/MECHANIC_RUNTIME_PROFILE.json`
- Violations return HTTP 403 with structured `mechanic_enforcement` payload

## Artifacts

| File | Schema |
|------|--------|
| `process_genome.v1.json` | `process_genome.v1` |
| `mechanic_scan.v1.json` | `mechanic_scan.v1` |
| `target_workflow.v1.json` | `target_workflow.v1` |
| `patch_plan.v1.json` | `patch_plan.v1` |
| `MECHANIC_RUNTIME_PROFILE.json` | `mechanic.runtime_profile.v1` |
| `reconstruction_plan.v1.json` | `mechanic.reconstruction.v1` |
| `report.md` | operator markdown (`--mode report --write-json`) |
| `mechanic_apply_review.json` | apply-review receipt |

## Example

```bash
python -m mechanic --mode scan --case-id acme-001 --repo-path ./customer-repo --trace-path ./traces/run.ndjson --write-json
python -m mechanic --mode diagnose --case-id acme-001 --write-json
python -m mechanic --mode rebuild --case-id acme-001 --write-json
python -m mechanic --mode report --case-id acme-001 --write-json
python -m mechanic --mode apply-review --case-id acme-001 --create-review --write-json
python -m mechanic --mode verify --case-id acme-001 --write-json
```

## Safety (MA-13)

Rebuild and apply proposals are **provisional**. Raw `apply` remains blocked (Class III prevention).
