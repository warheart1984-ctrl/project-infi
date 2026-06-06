# UGR Contribution Discovery Contract (v1.1)

Governed Proof-of-Discovery for six contribution types under URG cloud law.

## Contribution types

| Type | Payload anchors |
|------|-----------------|
| `subsystem` | `role`, `io_shape`, `rail_class`, `risk_ceiling`, `tenant_class` |
| `workflow` | `workflow_id`, `run_id`, `step_count` |
| `organ` | `organ_id`, `governance_mission_id` |
| `proof` | `proof_path` or `gene`, `claim_label` |
| `invariant` | `mission_id`, `invariant_digest`, `all_passed` |
| `capability` | `trace_id`, `module`, `action`, `ok` |
| `substrate` | `claim_id` or `surface`, `substrate_id` |

## Canonical ID

`contribution_id = SHA256(contribution_type + stable_json(normalized_payload))`

## API

| Method | Path |
|--------|------|
| POST | `/api/ugr/discover/contribution` |
| POST | `/api/ugr/discover/subsystem` (legacy alias) |
| GET | `/api/ugr/discover/contribution/<id>?tenant_id=` |

## Implementation

- `src/ugr/discovery/contribution_discovery.py`
- `src/ugr/discovery/validators/`
