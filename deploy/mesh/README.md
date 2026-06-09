# Mesh federation smoke stack (Phase 4)

Two-node Docker Compose stack: **AAIS mesh** (`project-infi`) and **rex-node** (`reasoning-exchange-node`) exchanging falsity ledger entries and invariant bundles over HTTP gossip.

## Prerequisites

- Docker Compose v2
- Sibling checkout: `reasoning-exchange-node` next to `project-infi` (compose build context expects `../../../reasoning-exchange-node`)

## Start

From the repo root:

```bash
docker compose -f deploy/mesh/docker-compose.federation.yml up --build
```

Services:

| Service     | Host port | Health |
|-------------|-----------|--------|
| `aais-mesh` | 5000      | `GET /api/mesh/health` |
| `rex-node`  | 5001      | `GET /api/mesh/health` |

Peer URLs are injected via `MESH_PEERS_JSON` in `docker-compose.federation.yml`.

## Operator curl sequence

### 1. Health

```bash
curl -s http://localhost:5000/api/mesh/health | jq .
curl -s http://localhost:5001/api/mesh/health | jq .
```

### 2. Identity and topology

```bash
curl -s http://localhost:5000/api/mesh/identity | jq .
curl -s http://localhost:5001/api/mesh/identity | jq .
curl -s http://localhost:5000/api/mesh/topology | jq .
curl -s http://localhost:5001/api/mesh/known-peers | jq .
```

### 3. Trigger gossip round (optional)

```bash
curl -s -X POST http://localhost:5000/api/mesh/gossip/run | jq .
curl -s -X POST http://localhost:5001/api/mesh/gossip/run | jq .
```

### 4. Push falsity entry (peer B → AAIS)

Replace `REX_NODE_ID` with the `node_id` from rex `GET /api/mesh/identity`.

```bash
curl -s -X POST http://localhost:5000/api/mesh/gossip \
  -H "Content-Type: application/json" \
  -H "X-Mesh-Peer-Id: REX_NODE_ID" \
  -d '{
    "push_entries": [{
      "claim_fingerprint": "operator-fp-001",
      "claim_text": "example refuted claim",
      "status": "refuted",
      "confidence": 0.9,
      "source_node_id": "REX_NODE_ID"
    }]
  }' | jq .
```

### 5. Push invariant bundle

```bash
curl -s -X POST http://localhost:5000/api/mesh/gossip \
  -H "Content-Type: application/json" \
  -H "X-Mesh-Peer-Id: REX_NODE_ID" \
  -d '{
    "invariants": {
      "bundle_id": "operator-bundle",
      "version": "2.0",
      "rules": [
        {"id": "min_confidence", "value": 0.75},
        {"id": "reject_known_false", "value": true}
      ]
    }
  }' | jq .
```

### 6. Read invariants export

```bash
curl -s http://localhost:5000/api/mesh/invariants | jq .
curl -s http://localhost:5001/api/mesh/invariants | jq .
```

## Automated tests

```powershell
python -m pytest tests/test_mesh_api.py tests/test_mesh_federation_live.py -q
```

From `reasoning-exchange-node`:

```powershell
python -m pytest tests/ -q
```

## Related docs

- [`docs/contracts/MESH_PEER_PROTOCOL.md`](../../docs/contracts/MESH_PEER_PROTOCOL.md)
- [`peers.example.json`](peers.example.json)
