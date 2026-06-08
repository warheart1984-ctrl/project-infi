# Peer Substrate Federation Contract

Version: `peer_substrate_federation.v1`

## Purpose

Defines how Infinity Pilot / AAIS instances register and communicate with **real peer substrates** for cross-substrate diplomacy (Stage 19), beyond in-repo test scopes.

## Configuration

| Variable | Description |
|----------|-------------|
| `AAIS_PEER_BASE_URLS` | Comma-separated peer base URLs (e.g. `https://peer-a.example:8000,https://peer-b.example:8000`) |
| `AAIS_PEER_TRUST_BUNDLE_PIN` | Optional SHA-256 pin of peer trust bundle manifest |
| `AAIS_TENANT_ID` | Local tenant identity for membrane-scoped federation |

## Peer registry entry shape

```json
{
  "peer_id": "peer_infinity_pilot_b",
  "base_url": "https://peer-b.example:8000",
  "trust_bundle_ref": "trustbundle://peer-b/2026-06-01",
  "accord_version": "operator_substrate_accord.v1",
  "revocation_epoch": null,
  "substrate_scopes": ["ul_substrate", "memory_overlay"]
}
```

## Outbound operations

- **Observe**: `POST {base_url}/api/operator/diplomacy/observe` with tenant membrane headers
- **Adopt accord**: `POST {base_url}/api/operator/diplomacy/accords/adopt` — requires bilateral operator approval on both sides

## Invariants

- Peers must respond with HTTP status `< 500` for chaos preflight; live Stage 19 proof rejects mock-only peers when `STAGE19_REQUIRE_LIVE=1`.
- Trust bundle pin mismatch blocks outbound adopt.
- Revoked peers (non-null `revocation_epoch`) are excluded from observe/adopt fan-out.

## Related

- [`inter_substrate_diplomacy_runtime.py`](../../src/inter_substrate_diplomacy_runtime.py)
- [`peer_substrate_client.py`](../../src/peer_substrate_client.py)
- Issue [#2](https://github.com/warheart1984-ctrl/Project-Infinity1/issues/2) — async diplomacy workflow
