# Forge Contractor

Forge is the bounded contractor service for AAIS.

## Boundary

- Separate HTTP service and port: `FORGE_PORT` defaults to `6060`
- Separate storage root: `FORGE_STORAGE` defaults to `.runtime/forge`
- No imports from `src/*`
- Contractor lane only through `POST /contractor`
- Forge does not run code, run tests, apply patches, validate repos, compute scores, or manage sandboxes
- Every response now carries a Foundation Law envelope plus an AAIS-UL snapshot

## Start

```powershell
.\.venv\Scripts\python.exe .\start_forge.py
```

## Health

- `GET /health`
- `GET /forge/health`

## Request Contract

```json
{
  "task_id": "forge-task-1",
  "kind": "generate_diff",
  "context": {
    "files": [
      {
        "path": "src/api.py",
        "content": "..."
      }
    ],
    "goal": "Refactor this route for clarity",
    "no_execution_without_handoff": true,
    "constraints": {
      "language": "python",
      "style": {
        "quotes": "single"
      },
      "max_output_chars": 20000
    }
  }
}
```

## Success Contract

```json
{
  "ok": true,
  "task_id": "forge-task-1",
  "kind": "generate_diff",
  "result": {
    "diffs": [
      {
        "path": "src/api.py",
        "unified_diff": "diff --git ..."
      }
    ]
  },
  "law_enforcement": {
    "contract_version": "aais.forge.ul.v1",
    "origin_integrity": {
      "forge_processed": true,
      "admission_status": "approved"
    },
    "execution_governance": {
      "action_permission_check": "review_only_handoff_required"
    },
    "violation_state": {
      "containment_state": "review_only_handoff"
    }
  },
  "ul_snapshot": {
    "count": 5,
    "sections": ["runtime_context", "mission_context", "workspace_context", "protocol_trace", "guardrail_state"]
  }
}
```

## Error Contract

```json
{
  "ok": false,
  "task_id": "forge-task-1",
  "kind": "generate_diff",
  "error": {
    "code": "law_violation",
    "message": "human-readable explanation"
  },
  "law_enforcement": {
    "contract_version": "aais.forge.ul.v1",
    "violation_state": {
      "violation_recorded": true,
      "blocking_law_id": "law_2_execution_governance",
      "containment_state": "contained"
    }
  },
  "ul_snapshot": {
    "count": 5,
    "sections": ["runtime_context", "mission_context", "workspace_context", "protocol_trace", "guardrail_state"]
  }
}
```

## AAIS Routes

The main AAIS Flask app exposes Forge through:

- `POST /api/jarvis/forge/code`
- `POST /api/jarvis/forge/evaluate` for the separate ForgeEval lane

The contractor route builds bounded workspace context, calls Forge over HTTP, and returns the contractor result plus a Forge context summary. It now also exposes the Forge Foundation Law envelope and UL snapshot at the AAIS route layer so the documented governance state stays inspectable. ForgeEval stays separate and is never mixed into the contractor payload.
