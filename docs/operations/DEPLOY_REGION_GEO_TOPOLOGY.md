# Deploy region geo topology — Project Infinity

Operators planning the Azure pilot often juggle **three different “region” vocabularies** in this repo:

| Layer | Example IDs | Source |
|-------|-------------|--------|
| Azure footprint | `eastus2`, `westus2` | [`.azure/deployment-plan.md`](../../.azure/deployment-plan.md) |
| Firebase vector backend | `us-central1` | [`deploy/firebase-data-connect/dataconnect/dataconnect.yaml`](../../deploy/firebase-data-connect/dataconnect/dataconnect.yaml) |
| UGR organ policy | `tenant-us`, `tenant-eu` | [`deploy/ugr/tenants/tenant-acme/provider-organs.json`](../../deploy/ugr/tenants/tenant-acme/provider-organs.json) |

Those strings are not interchangeable. A single **geographic map** makes cross-region latency and policy alignment visible before `azure-deploy` — especially when Firebase memory projection and Azure ACA run in different clouds.

This artifact uses the **Amazon Location Service** plugin patterns (resourceless Maps API + MapLibre).

---

## Deliverables in this repo

| Path | Purpose |
|------|---------|
| [`deploy/geo/regions.json`](../../deploy/geo/regions.json) | Canonical region registry with `[lon, lat]` and provenance |
| [`deploy/geo/operator-deploy-region-map.html`](../../deploy/geo/operator-deploy-region-map.html) | Interactive MapLibre viewer (operator-facing) |

---

## Why Amazon Location Service here

- **Resourceless `geo-maps:GetTile`** — no pre-created map resources; fits pilot-style deploy docs.
- **Same auth model as Places/Routes** — API keys for browser maps; IAM for server geocode refresh.
- **MapLibre-native** — aligns with plugin guidance (`validateStyle: false`, direct style descriptor URL).
- **Complements Zscaler preflight** — if operators view this map from a locked-down workstation, `maps.geo.*.amazonaws.com` must be allowed (see below).

---

## API key setup (resourceless)

Create an API key in the AWS console (Location Service → API keys) with:

| AllowActions | AllowResources |
|--------------|----------------|
| `geo-maps:GetTile` | `arn:aws:geo-maps:us-east-1::provider/default` |

Optional (refresh coordinates from addresses):

| AllowActions | AllowResources |
|--------------|----------------|
| `geo-places:Geocode` | `arn:aws:geo-places:us-east-1::provider/default` |

Do **not** use legacy `geo:GetMap*` actions — they apply to pre-created map resources only.

Store the key outside git. For local map viewing:

```text
file:///e:/project-infi/deploy/geo/operator-deploy-region-map.html?key=YOUR_KEY
```

Or persist in browser: `localStorage.amazonLocationApiKey = '...'`.

---

## Zscaler / egress note

If you open the map from the same Zscaler-protected workstation used for Azure deploy, add to [ZSCALER_EGRESS_PREFLIGHT.md](./ZSCALER_EGRESS_PREFLIGHT.md) checks:

| Host | Workstation task | Risk if blocked |
|------|------------------|-----------------|
| `maps.geo.us-east-1.amazonaws.com` | Load deploy region map tiles | Blank map in operator topology view |
| `unpkg.com` / `cdn.jsdelivr.net` | MapLibre GL assets (first load) | Map shell without renderer |

---

## Refresh coordinates with Geocode (optional)

When `AMAZON_LOCATION_API_KEY` and region are set, you can re-resolve `geocode_query` fields from `regions.json` via `geo-places:Geocode` (forward geocode). Example request shape:

```bash
aws geo-places geocode \
  --query-text "Iowa, United States" \
  --key YOUR_API_KEY \
  --region us-east-1
```

Response positions use **[longitude, latitude]** (GeoJSON order). Update `deploy/geo/regions.json` after operator confirms Azure region choice.

---

## Placement in deployment checklist

Insert after Zscaler egress preflight and before region confirmation in [`.azure/deployment-plan.md`](../../.azure/deployment-plan.md):

- [ ] Review deploy region topology map with stakeholders
- [ ] Confirm single Azure region (`eastus2` **or** `westus2`, not both for pilot)
- [ ] Document cross-cloud hop: Azure ACA ↔ Firebase `us-central1` if `AAIS_VECTOR_BACKEND=firebase`
- [ ] Verify UGR `allowed_regions` still match chosen Azure geography

---

## AWS MCP server

The Amazon Location Service plugin includes the **aws-mcp** server for live API calls and doc lookup. It is not yet wired in this workspace MCP folder — configure per [AWS MCP getting started](https://docs.aws.amazon.com/aws-mcp/latest/userguide/getting-started-aws-mcp-server.html) to geocode or route-check from Cursor without leaving the repo.
