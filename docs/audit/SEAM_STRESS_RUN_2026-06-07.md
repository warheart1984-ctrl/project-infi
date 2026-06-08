# Seam Stress Run — 2026-06-07

## Operator summary

- Base: `http://127.0.0.1:8000`
- Offline harvest: `False`
- Total probes: `221`
- Failures: `0`
- Critical/high: `0`

## Health

```json
{
  "reachable": true,
  "status_code": 200,
  "healthy": true,
  "legacy_api_loaded": true,
  "legacy_api_mount_error": null,
  "degraded": false
}
```

## Findings

| Endpoint | Status | Severity | Seam class | Closure |
|----------|--------|----------|------------|---------|
| _none_ | — | — | — | closed |

## Genome gaps (declared API missing from Flask)

- GET /api/operator/organs/business_workflows (workflow_family_business)
- GET /api/operator/organs/creative_workflows (workflow_family_creative)
- GET /api/operator/organs/data_workflows (workflow_family_data)
- GET /api/operator/organs/knowledge_work (workflow_family_knowledge)
- GET /api/operator/organs/operational_workflows (workflow_family_ops)
- GET /api/operator/organs/personal_workflows (workflow_family_personal)

## Seam records

- none (clean run)

## Chat pressure

```json
{
  "identity_stable": true,
  "turns": [
    {
      "turn": 1,
      "status": 200,
      "reply_len": 0
    },
    {
      "turn": 2,
      "status": 200,
      "reply_len": 0
    },
    {
      "turn": 3,
      "status": 200,
      "reply_len": 0
    }
  ],
  "long_turn": {
    "status": 200,
    "reply_len": 0,
    "truncated_suspected": false
  }
}
```
