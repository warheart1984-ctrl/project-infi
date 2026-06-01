# Mechanic Hosted Pilot

Mechanic is positioned as an AI workflow OBD scanner for AI platform teams.
The pilot promise is simple: install against a repository, ingest optional AI
trace evidence, run a governed scan within the 5 minute pilot SLA, and return
an evidence-backed report that names runtime risk, automation boundaries, and
human sign-off requirements.

The hosted pilot keeps the local engine intact. Hosted workers run the existing
`scan -> diagnose -> rebuild -> report -> verify` path in an injected artifact
directory, never in `.runtime/mechanic/`, and never mutate customer repositories.

## Pilot Package

- GitHub App first; GitLab is deferred.
- Up to 5 repositories per pilot customer.
- Optional trace import for LangSmith, n8n, Make, Cursor-style exports, and
  generic JSON/NDJSON traces.
- Evidence bundles with artifact hashes.
- OBD report for AI platform owners.
- Review-gated remediation proposals only.

## SLA Defaults

- Scan starts within 60 seconds after queue admission.
- Scan completes within 300 seconds for repos inside configured pilot limits.
- Critical or high MA-13 class II/III findings require human sign-off.
- Raw apply remains blocked.

## Local Deployment

Run the hosted API locally:

```bash
python -m mechanic.hosted
```

Default service URL:

```text
http://127.0.0.1:8765
```

Run the production-style stack:

```bash
cd mechanic/hosted/deploy
docker compose up --build
```

Run the no-credentials external stub smoke:

```bash
python -m mechanic.hosted.smoke
```

This exercises the hosted service with local substitutes for GitHub checkout,
S3 artifact publication, and the production-style scan path. It is the default
preflight when Docker, MinIO, Postgres, or live GitHub credentials are not
available.

The compose stack starts:

- `mechanic-api`: FastAPI hosted API.
- `mechanic-worker`: Redis-backed worker fleet entrypoint.
- `postgres`: persistent hosted state.
- `redis`: worker queue substrate.
- `minio`: S3-compatible artifact backend for local production rehearsal.

Configured endpoints:

- `POST /v1/installations/github/callback`
- `POST /v1/scans`
- `GET /v1/scans/{scan_id}`
- `GET /v1/scans/{scan_id}/report`
- `GET /v1/scans/{scan_id}/artifacts`
- `POST /v1/traces/import`
- `POST /v1/scans/{scan_id}/replay`

## Environment

- `MECHANIC_ARTIFACT_ROOT`: artifact root; defaults to `.runtime/mechanic-hosted`.
- `MECHANIC_DATABASE_URL`: Postgres connection string for production.
- `MECHANIC_HOSTED_DB`: SQLite database path.
- `MECHANIC_ARTIFACT_BACKEND`: `filesystem` or `s3`.
- `MECHANIC_S3_BUCKET`: bucket for S3/MinIO artifacts.
- `MECHANIC_S3_ENDPOINT_URL`: optional S3-compatible endpoint.
- `MECHANIC_REDIS_URL`: Redis URL for worker fleet mode.
- `MECHANIC_HOSTED_API_KEY_SHA256`: optional SHA-256 hash for `X-API-Key`.
- `MECHANIC_ARTIFACT_SIGNING_SECRET`: local signed artifact token secret.
- `MECHANIC_GITHUB_WEBHOOK_SECRET`: verifies `X-Hub-Signature-256`.
- `MECHANIC_GITHUB_APP_ID`: GitHub App id.
- `MECHANIC_GITHUB_PRIVATE_KEY_PATH`: path to GitHub App private key.
- `MECHANIC_GITHUB_CHECKOUT_ROOT`: local checkout scratch root.
- `MECHANIC_CI_REPLAY_COMMAND`: command hook for CI replay.
- `MECHANIC_SECOND_MACHINE_REPLAY_COMMAND`: command hook for second-machine replay.

## Storage And Security

The pilot uses SQLite locally or Postgres in deployment for customers,
installations, scan jobs, evidence bundles, and artifact metadata. Artifacts are
tenant and scan scoped under the artifact root. The filesystem backend signs
artifact references with an HMAC token; the S3 backend mirrors finished scan
directories to S3/MinIO and emits presigned object URLs.

Webhook verification uses GitHub's `sha256=` HMAC signature. API auth is a
hashed shared key for the pilot. Evidence artifacts are scrubbed for common
secret/token shapes before bundle publication, and audit events are written as
JSONL under the artifact root.

## GitHub App

The GitHub callback accepts either the pilot contract or native GitHub webhook
payload shape. Production installs should configure:

- GitHub App id.
- GitHub App private key.
- Webhook secret.
- Least-privilege repository permissions: `contents:read`, `metadata:read`.

The `GitHubAppClient` can verify webhooks, exchange an installation id for a
read-scoped installation token, and checkout repositories with a short-lived
installation token. `PyJWT` is required for GitHub App JWT signing.

To run a GitHub checkout scan through the API, submit a scan with:

```json
{
  "installation_id": "123456",
  "repo_ref": "main",
  "checkout": true
}
```

`repo_path` remains available for local/operator-controlled checkouts.

## External Stubs

`mechanic.hosted.stubs` provides:

- `StubGitHubAppClient`: copies a local fixture repo instead of calling GitHub.
- `StubArtifactStore`: emits signed `stub-s3://` artifact references.
- `create_stubbed_service`: builds a hosted service with those stubs attached.

These stubs are for smoke tests, demos, and CI environments without external
credentials. They must not be used as production security substitutes.

## Replay Tiers

Local replay is available by default and promotes evidence to `local_proven`
when genome and scan hashes match.

CI and second-machine replay require explicit runner commands. If those runner
commands are missing, Mechanic records the tier as `asserted` with
`external_runner_unavailable: true` instead of overstating proof.

Runner commands receive:

```text
<repo_path> <artifact_dir> <trace_path>
```

and must exit `0` to promote the tier.

## Security Hardening

- API key auth via `X-API-Key` and SHA-256 hash.
- GitHub webhook HMAC verification.
- Request size limit and simple per-minute rate limiting.
- `no-store`, `nosniff`, and `no-referrer` response headers.
- Secret scrubbing before evidence bundle publication.
- Tenant/scan artifact path scoping.
- Append-only hosted audit log.

## Pilot Runbook

1. Create a customer installation through the GitHub callback.
2. Submit a scan with repo checkout path, branch/ref, and optional trace inputs.
3. Review the OBD report for risk, owner, remediation class, and sign-off need.
4. Retrieve the evidence bundle and signed artifact references.
5. Run CI or second-machine replay when runner hooks are configured.
6. Use `apply-review` only for proposal records; direct apply remains blocked.

## Pricing Skeleton

- Pilot: 5 repos, 5 minute scan SLA target, trace import, evidence bundles.
- Team: more repos, scheduled scans, CI replay.
- Enterprise: second-machine replay, custom retention, SSO, dedicated runner pool.
