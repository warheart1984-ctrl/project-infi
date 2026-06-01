# Proof Federation Protocol v1

Authority: [PLATFORM_MEMBRANE_V3_SPEC.md](../../runtime/PLATFORM_MEMBRANE_V3_SPEC.md).

## AttestationSubmit

```json
{
  "job_id": "job-xxx",
  "runner_id": "primary",
  "region": "us",
  "result_hash": "<sha256 hex>",
  "manifest_ref": "docs/proof/platform/cross_machine/REPLAY_MANIFEST.v2.template.json",
  "signature": "<hmac-sha256 hex, v25>"
}
```

Schema: `platform/schemas/proof_attestation.v1.json`.

## Quorum rule

- `distinct_runner_id >= PLATFORM_PROOF_QUORUM` (default 2)
- All attestations share the **same** `result_hash`
- On success: `proof_status=proven`, `claim_label=proven`
- On hash mismatch: `proof_status=disputed`, spawn `drift_investigation` Class II (v26)

## Workflow gate

When advancing `workflow_run`, if next step kind ∈ `PROOF_REQUIRED_KINDS` and parent job quorum not met → parent/workflow `blocked_proof`.

## Runner registry (v27)

Table `proof_runners`. When `PLATFORM_ENFORCE_RUNNER_REGISTRY=1`, reject unknown `runner_id`.

Enrollment: `POST /v1/proof/runners/enroll` (platform_admin).

## Replay manifests

| Version | File | Shape |
|---------|------|-------|
| v1 | `REPLAY_MANIFEST.template.json` | `commands[]` |
| v2 | `REPLAY_MANIFEST.v2.template.json` | `runners[{ runner_id, region, commands }]` |

[`platform/replay.py`](../../../platform/replay.py) supports both.

## APIs

- `POST /v1/jobs/{job_id}/attestations` — scope `proof:attest`
- `GET /v1/jobs/{job_id}/attestations`
- `GET /v1/proof/federation/{federation_id}`

## CI (v28)

Primary, secondary, tertiary runners submit attestations; tertiary job fails on hash mismatch.

## v3 — Asymmetric attestations (v35–v36)

| Field | Values |
|-------|--------|
| `signature_alg` | `hmac-sha256` (default dev), `ed25519` |
| `public_key_ref` | Runner registry pointer or inline `public_key_pem` |

Message signed (Ed25519): `{job_id}:{runner_id}:{result_hash}` UTF-8 bytes.

Env: `PLATFORM_ATTESTATION_ALG` (`hmac-sha256` | `ed25519`).

### Attestation bundle

- `GET /v1/jobs/{job_id}/attestations/bundle`
- Schema: `platform/schemas/proof_attestation_bundle.v1.json`

### Replay v3

Manifest `platform.platform_replay_manifest.v3` adds optional `post_attestation_url` per runner.

[`platform/replay.py`](../../../platform/replay.py) helper `post_replay_attestations(report, base_url, api_key)`.

## Implementation

- [`platform/proof/federation.py`](../../../platform/proof/federation.py)
- [`platform/proof/quorum.py`](../../../platform/proof/quorum.py)
- [`platform/proof/signing.py`](../../../platform/proof/signing.py)
- [`platform/proof/bundles.py`](../../../platform/proof/bundles.py)
