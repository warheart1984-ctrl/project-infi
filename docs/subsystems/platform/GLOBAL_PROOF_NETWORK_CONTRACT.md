# Global Proof Network Contract v1

Authority: [PLATFORM_MEMBRANE_V5_SPEC.md](../../runtime/PLATFORM_MEMBRANE_V5_SPEC.md).

## Witness registry (v43)

Table `proof_witnesses`: `{ witness_id, region, public_key_ref, status }`.

- `POST /v1/proof/witnesses/enroll` (platform_admin)
- When `PLATFORM_WITNESS_REQUIRED=1`, job-level promotion requires witness co-attestation count `max(1, PLATFORM_WITNESS_QUORUM)` (runner attestations may still be recorded)

## Attestation graph (v44)

- `GET /v1/proof/network/graph?job_id=`
- Nodes: runners, witnesses; edges: attestations

## Quorum

Runner quorum (existing) AND optional `PLATFORM_WITNESS_QUORUM` witness count.

## Implementation

- [`platform/proof/witnesses.py`](../../../platform/proof/witnesses.py)
