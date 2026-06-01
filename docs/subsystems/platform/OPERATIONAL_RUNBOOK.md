# Platform Membrane Operational Runbook

## Start (local dev)

```bash
export PLATFORM_MASTER_API_KEY=dev-master-key-change-me
export PLATFORM_DATABASE_URL=sqlite:///.runtime/platform/platform.sqlite3
python -m platform serve
```

## Start (compose)

```bash
cd deploy/platform
cp .env.example .env
docker compose up --build
```

## Infinity Pilot (full stack)

```bash
cd deploy/pilot
cp .env.example .env
docker compose up --build -d
python ../../scripts/pilot_compose_smoke.py --base-url http://127.0.0.1:8090 --api-key <PLATFORM_MASTER_API_KEY>
```

See [INFINITY_PILOT_EARLY_ADOPTER.md](../../operations/INFINITY_PILOT_EARLY_ADOPTER.md).

## Bootstrap org + API key

1. Set `PLATFORM_MASTER_API_KEY` in environment.
2. `POST /v1/orgs` with master key as `X-Api-Key`.
3. `POST /v1/orgs/{org_id}/api-keys` to issue operator key.

## Verify

```bash
make platform-gate
make platform-smoke
curl -s http://127.0.0.1:8090/v1/health
```

## Backup and export

- Postgres: volume snapshot `pilot_pg` / `platform_pg`.
- Audit JSONL: `PLATFORM_AUDIT_PATH` or `.runtime/platform/audit/`.
- Operational ledger: `python -m platform ledger export --org <org_id>`.
- Sovereign pack: `POST /v1/orgs/{org_id}/sovereign/export-pack`.

## Rollback

1. `docker compose down` (pilot or platform profile).
2. Restore Postgres volume from snapshot.
3. Revoke API keys via org admin routes.

## Kill-switch

1. Stop `platform-worker` services.
2. Set `PLATFORM_REQUIRE_API_KEY=1` and rotate master key.
3. Disable webhook subscriptions per org.

## Failsafe

- Stop worker before DB maintenance.
- Cross-org access attempts are logged and denied.
- Do not delete subsystem `.runtime` trees without artifact index purge.
- `PLATFORM_WITNESS_REQUIRED=1` only when ops intends witness quorum.

## Debt

See PLAT-D1..D34 and PLAT-PILOT-D1 in [NOVA_CAPABILITY_INVENTORY.md](../../runtime/NOVA_CAPABILITY_INVENTORY.md).
