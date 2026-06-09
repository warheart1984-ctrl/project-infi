# PLAT-D8 OIDC integration — scope proof (v1)

Status: **partial** (stub org E2E proven; production IdP token exchange open)

CISIV stage: **implementation** (partial)

## Claim

| Item | Label | Evidence |
|------|-------|----------|
| OIDC login/callback routes on Platform membrane | proven | `platform/v814_routes.py` — `patch_oidc_routes` |
| Provider registry (Google, Microsoft, GitHub, local) | proven | `platform/auth/oidc_providers.py` |
| Session token issuance after callback | proven | `platform/auth/oidc.py` — `issue_session_token` |
| Per-org `oidc_provider` + `oidc_config` on org record | proven | `platform/billing/engine.py` default shape; org upsert |
| One org stub IdP E2E (login → callback → session) | proven | `tests/test_platform_v814.py::test_oidc_stub_org_e2e` |
| Real token exchange (non-stub) in production | **asserted** | `PLATFORM_OIDC_STUB=1` default; stub identity in `exchange_code_for_identity` |
| One production org IdP end-to-end (live authorize → token → session) | **open** | Requires `PLATFORM_OIDC_STUB=0` + registered redirect URI |

## Stub org E2E (2026-06-08)

Automated proof for a single test org with `oidc_provider=github` and stub token exchange:

```powershell
Set-Location e:\project-infi
& "C:\Users\randj\AppData\Local\Programs\Python\Python312\python.exe" -m pytest tests/test_platform_v814.py::test_oidc_stub_org_e2e -q
```

Flow exercised:

1. Create org via `POST /v1/orgs`
2. Set `oidc_provider` + `oidc_config.client_id` on org record
3. `GET /v1/auth/oidc/{org_id}/login` → authorize URL + state
4. `GET /v1/auth/oidc/callback?org_id=…&code=…` → `access_token` + `principal_id`

## Per-org IdP runbook (org admin)

1. Register redirect URI with IdP: `{PLATFORM_BASE}/v1/auth/oidc/callback` (default dev: `http://127.0.0.1:8090/v1/auth/oidc/callback`).
2. Set org fields (platform admin or store upsert):
   - `oidc_provider`: `google` | `microsoft` | `github` | `local`
   - `oidc_config.client_id`: IdP application client ID
   - `oidc_config.client_secret`: store in env/secret manager (not in org JSON for production)
3. Env for membrane:
   - `PLATFORM_OIDC_REDIRECT_URI` — must match IdP registration
   - `PLATFORM_OIDC_{PROVIDER}_CLIENT_ID` — fallback when org config omits client_id
   - `PLATFORM_OIDC_STUB=0` — enable real token exchange (when implemented)
4. Verify: operator hits login URL, completes IdP consent, callback returns session token; confirm principal row in org.

## What remains (PLAT-D8 full closure)

1. **Real HTTP token exchange** when `PLATFORM_OIDC_STUB=0` — provider token endpoints + JWKS/userinfo validation.
2. **Live org capture** — redacted audit of one real IdP round-trip (not stub).
3. **Pilot checklist** — move PLAT-D8 from `partial` → `closed` in baseline checklist after item 2.

## Reproduction (local stub path)

```bash
# Platform stack up (see INFINITY_PILOT_EARLY_ADOPTER.md)
curl -s "http://127.0.0.1:8090/v1/auth/oidc/{org_id}/login"
# Follow redirect; callback issues session when PLATFORM_OIDC_STUB=1 (default)
```

## Debt tracker update

Baseline: [`INFINITY_PILOT_BASELINE_CHECKLIST.md`](../../baseline/INFINITY_PILOT_BASELINE_CHECKLIST.md) — PLAT-D8 remains **partial** until live IdP E2E (item 2 above).

## Related

- [`platform/auth/oidc.py`](../../../platform/auth/oidc.py)
- [`platform/auth/oidc_providers.py`](../../../platform/auth/oidc_providers.py)
- [`platform/v814_routes.py`](../../../platform/v814_routes.py)
