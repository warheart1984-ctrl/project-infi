# Mesh Peer Protocol

Version: `mesh_peer_protocol.v1`

## Purpose

Defines HTTP interactions between **reasoning mesh nodes** (AAIS `project-infi` and standalone `reasoning-exchange-node`) for:

- Ed25519-style handshake and peer registration
- Falsity ledger sync (gossip)
- Invariant bundle propagation
- Capability-gated inbound gossip from known peers

This is distinct from [Peer Substrate Federation](PEER_SUBSTRATE_FEDERATION_CONTRACT.md) (operator diplomacy / Stage 19).

## Base URL and headers

| Header | Required | Description |
|--------|----------|-------------|
| `Content-Type` | POST bodies | `application/json` |
| `X-Mesh-Peer-Id` | Inbound gossip from peers | Remote node id; enables `falsity_sync` capability check |
| `X-Mesh-Peer-Url` | Handshake ACK (optional) | Caller base URL for pinning known peers |

## Capabilities

Nodes advertise capabilities in `mesh_config.json` and handshake records:

| Capability | Meaning |
|------------|---------|
| `reasoning_evaluate` | May call evaluate endpoints that honor mesh governance |
| `falsity_sync` | May POST gossip with falsity pushes |
| `invariant_propagate` | May push invariant bundles via gossip |
| `handshake` | Supports mesh handshake endpoints |

Inbound gossip with `X-Mesh-Peer-Id` requires the peer to be known (handshake) and to have `falsity_sync`.

## Endpoints

### `GET /api/mesh/health`

Liveness: node id, mesh data directory, gossip daemon status.

### `GET /api/mesh/identity`

Public node record: `node_id`, `fingerprint`, `verify_key`, `node_name`.

### `GET /api/mesh/topology`

Configured and known peers, capabilities, trust scores.

### `GET /api/mesh/known-peers`

Persisted handshake registry entries.

### `GET /api/mesh/invariants`

Current invariant bundle export (digest + rules).

### `POST /api/mesh/handshake`

**Request:** `{ "phase": "HELLO", "node": { ... public node record ... } }`

**Response:** `{ "phase": "CHALLENGE", "challenge_id": "...", "nonce": "..." }`

Pending challenges are persisted with a 5-minute TTL.

### `POST /api/mesh/handshake/ack`

**Request:** `{ "phase": "ACK", "challenge_id": "...", "signature": "...", "node": { ... } }`

On success, registers the remote peer in `known_peers` and returns ledger/invariant heads for sync.

### `POST /api/mesh/gossip`

Bidirectional sync body:

```json
{
  "falsity_head": "<optional known head>",
  "push_entries": [ { "claim_fingerprint": "...", "claim_text": "...", "reason": "..." } ],
  "invariants": { "bundle_id": "...", "version": "2.0", "rules": [] }
}
```

**Response:**

```json
{
  "falsity_head": "<sha256 of last ledger entry>",
  "falsity_entries": [ "... entries since known head ..." ],
  "invariants": { "... merged bundle ..." },
  "invariant_digest": "<sha256>"
}
```

Falsity merge modes:

- **`with_claim_text`** (default): full claim text recorded in RLS falsity registry; explicit `claim_fingerprint` is also registered when it differs from the text hash.
- **`fingerprint_only`**: registry entry by fingerprint only (no claim text).

Invariant merge adopts the remote bundle when version (semver-like tuple) or `updated_at` is newer.

### `POST /api/mesh/gossip/run`

Runs gossip pull against all configured + known peer URLs.

## Configuration

| Variable | Description |
|----------|-------------|
| `MESH_PEERS_JSON` | JSON array of `{ "url": "http://peer:port" }` merged into `mesh_config.json` peers |
| `MESH_DATA_DIR` | AAIS mesh-only server data root (compose) |
| `REX_MESH_DIR` | rex-node runtime root (state under `.mesh/`) |

Example peers file: [`deploy/mesh/peers.example.json`](../../deploy/mesh/peers.example.json).

## Gossip runtime

- Periodic gossip daemon with exponential backoff on failures
- Outbound gossip may require pinned `verify_key` when configured on peer records
- Graceful shutdown hooks stop the daemon thread

## Implementations

| Repo | Routes | Mesh state path |
|------|--------|-----------------|
| `project-infi` | `src/mesh/api_routes.py` | Flat under configured mesh dir |
| `reasoning-exchange-node` | `app.py` | `{base_dir}/.mesh/` |

## Related

- [`deploy/mesh/README.md`](../../deploy/mesh/README.md) — Docker Compose operator flow
- [`tests/test_mesh_federation_live.py`](../../tests/test_mesh_federation_live.py) — threaded AAIS + rex HTTP proof
