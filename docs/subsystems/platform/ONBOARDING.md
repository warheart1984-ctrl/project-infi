# Platform Onboarding — First 10 Minutes

## 1. Start platform API

```bash
export PLATFORM_MASTER_API_KEY=dev-master-key
python -m platform serve
```

## 2. Create org (master key)

```bash
curl -s -X POST http://127.0.0.1:8090/v1/orgs \
  -H "X-Api-Key: $PLATFORM_MASTER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"org_id":"acme","label":"Acme Corp"}'
```

## 3. Create operator API key

```bash
curl -s -X POST http://127.0.0.1:8090/v1/orgs/acme/api-keys \
  -H "X-Api-Key: $PLATFORM_MASTER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"principal_id":"op-1","roles":["operator"],"scopes":["jobs:submit","artifacts:read"]}'
```

Save the returned `api_key` (shown once).

## 4. Submit Mechanic scan job

```bash
export ACME_KEY=<api_key from step 3>
curl -s -X POST http://127.0.0.1:8090/v1/jobs \
  -H "X-Api-Key: $ACME_KEY" \
  -H "Content-Type: application/json" \
  -d @docs/subsystems/platform/examples/mechanic_scan.json
```

## 5. View in console

1. Open `http://127.0.0.1:3000/platform/getting-started`
2. Paste API key and set org `acme`
3. Open **Platform Ops** → jobs and artifacts

## Invite flow (admin)

```bash
curl -s -X POST http://127.0.0.1:8090/v1/orgs/acme/invites \
  -H "X-Api-Key: $PLATFORM_MASTER_API_KEY" \
  -d '{"email":"friend@example.com","role":"operator"}'
```

Send friend the `accept_url`. They accept with:

```bash
curl -s -X POST http://127.0.0.1:8090/v1/invites/accept \
  -d '{"token":"<token>","principal_id":"friend-1","display_name":"Friend"}'
```

## Debugging drifts (artifacts)

- Job detail → **Artifacts** tab
- Global **Artifacts** view at `/platform/artifacts`
- Use lineage endpoint: `GET /v1/artifacts/{ref_id}/lineage?org_id=acme`
