# Expected Output — Mission #002

## Successful `nova generate` (factorial)

```
export function factorial(n: number): number {
  ...
}

Receipts:
[
  {
    "id": "<uuid>",
    "timestamp": <number>,
    "action": { "type": "generate", "payload": { "prompt": "..." } },
    "invariantsChecked": ["no-credentials", "no-dangerous-shell"],
    "continuityHash": "<hex>",
    "ledgerHash": "<hex>"
  }
]
```

## Blocked `nova generate` (dangerous)

```
BLOCKED: Invariant violated: no-dangerous-shell — Disallow dangerous shell commands...

Receipts:
[
  {
    "blocked": true,
    "blockReason": "Invariant violated: no-dangerous-shell — ..."
  }
]
```

## Continuity Snapshot

```json
{
  "id": "<uuid>",
  "timestamp": <number>,
  "stateHash": "<sha256-hex>"
}
```

## Receipt JSON Schema

| Field | Type | Required |
|-------|------|----------|
| id | string (UUID) | yes |
| timestamp | number | yes |
| action | AgentAction | yes |
| invariantsChecked | string[] | yes |
| continuityHash | string | yes |
| ledgerHash | string | yes |
| blocked | boolean | no |
| blockReason | string | no |
