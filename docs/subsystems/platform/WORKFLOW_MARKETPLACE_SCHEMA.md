# Workflow Marketplace Schema v1

Authority: [PLATFORM_MEMBRANE_V3_SPEC.md](../../runtime/PLATFORM_MEMBRANE_V3_SPEC.md).

## Listing (`platform.workflow_listing.v1`)

| Field | Type | Notes |
|-------|------|-------|
| listing_id | string | Primary key |
| org_id | string | Publisher org |
| ugr_tenant_id | string | Tenant scope for `tenant` visibility |
| visibility | enum | `org`, `tenant`, `public` |
| curated | boolean | Required true for `public` (platform_admin) |
| semver | string | Semantic version |
| steps | array | See `platform.workflow_listing_step.v1` |
| approval_status | enum | v23: `draft`, `pending`, `published`, `deprecated` |
| proof_requirements | array | Job kinds requiring federation quorum |

## Step item (`platform.workflow_listing_step.v1`)

| Field | Required |
|-------|----------|
| subsystem | yes |
| kind | yes |
| params | no |
| proof_required | no |

## Visibility matrix

| visibility | List | Install |
|------------|------|---------|
| org | same org_id | same org_id |
| tenant | same ugr_tenant_id | same tenant |
| public | curated listings globally | any org (policy/billing still apply) |

## Installed workflow (store `workflows`)

| Field | Notes |
|-------|-------|
| source_listing_id | v18 install |
| installed_version | semver at install time |
| forked_from | optional fork |

## Metering (usage_daily)

| Field | Event |
|-------|-------|
| marketplace_installs | install |
| workflow_runs_from_listing | run |

## APIs

- `POST /v1/orgs/{org_id}/marketplace/listings`
- `POST /v1/marketplace/listings/{id}/approve` (v23)
- `POST .../install`, `.../fork`, `.../run`
- `GET /v1/orgs/{org_id}/marketplace/analytics` (v24)

## v33 — Reviews

Table `listing_reviews`: `{ review_id, listing_id, org_id, principal_id, rating, comment, created_at }`.

- `POST /v1/marketplace/listings/{listing_id}/reviews?org_id=`
- Analytics includes `average_rating`, `review_count`

## v34 — Catalog and semver upgrade

- `GET /v1/marketplace/catalog?org_id=&q=` — search visible listings by name
- `PATCH /v1/marketplace/listings/{listing_id}/version?org_id=` — body `{ semver, breaking }`

## Implementation

- [`platform/marketplace/`](../../../platform/marketplace/)
