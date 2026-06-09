-- CockroachDB bootstrap for project-infi platform persistence.
-- Generated from plugin guidance (cockroachdb-sql + designing-multi-region-applications).
--
-- Context: deploy/platform/docker-compose.yml runs platform-worker-us and platform-worker-eu
-- against a single ParadeDB/Postgres instance. This schema is the CockroachDB upgrade path:
--   - closes Postgres/SQLite table parity gaps in platform/store.py
--   - replaces SERIAL audit hotspot with UUID
--   - pins worker-coordination tables REGIONAL BY ROW (us/eu local writes)
--   - keeps org/principal lookups GLOBAL (low churn, read everywhere)
--
-- Prerequisite (run once per cluster):
--   ALTER DATABASE platform PRIMARY REGION "us-east1" REGIONS "us-east1", "europe-west1";
--
-- Connection: set PLATFORM_DATABASE_URL to the Cockroach postgres wire URL.
-- ParadeDB pg_search is NOT available here; keep BM25 in ParadeDB or use an external search index.

-- ---------------------------------------------------------------------------
-- Global reference tables (org identity, auth metadata)
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS orgs (
  org_id STRING PRIMARY KEY,
  payload JSONB NOT NULL
) LOCALITY GLOBAL;

CREATE TABLE IF NOT EXISTS principals (
  principal_id STRING PRIMARY KEY,
  org_id STRING NOT NULL,
  payload JSONB NOT NULL,
  INDEX principals_org_idx (org_id)
) LOCALITY GLOBAL;

CREATE TABLE IF NOT EXISTS api_keys (
  api_key_id STRING PRIMARY KEY,
  org_id STRING NOT NULL,
  principal_id STRING NOT NULL,
  key_hash STRING NOT NULL,
  payload JSONB NOT NULL,
  INDEX api_keys_org_idx (org_id),
  UNIQUE INDEX api_keys_hash_idx (key_hash)
) LOCALITY GLOBAL;

CREATE TABLE IF NOT EXISTS role_bindings (
  binding_id STRING PRIMARY KEY,
  org_id STRING NOT NULL,
  principal_id STRING NOT NULL,
  payload JSONB NOT NULL,
  INDEX role_bindings_org_principal_idx (org_id, principal_id)
) LOCALITY GLOBAL;

CREATE TABLE IF NOT EXISTS invites (
  invite_id STRING PRIMARY KEY,
  org_id STRING NOT NULL,
  token_hash STRING NOT NULL,
  payload JSONB NOT NULL,
  UNIQUE INDEX invites_token_hash_idx (token_hash)
) LOCALITY GLOBAL;

CREATE TABLE IF NOT EXISTS sessions (
  session_id STRING PRIMARY KEY,
  org_id STRING NOT NULL,
  payload JSONB NOT NULL,
  INDEX sessions_org_idx (org_id)
) LOCALITY GLOBAL;

-- ---------------------------------------------------------------------------
-- Regional workload tables (worker-local read/write in us + eu)
-- crdb_region defaults to gateway_region() for inserts from regional workers.
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS platform_jobs (
  job_id STRING NOT NULL,
  org_id STRING NOT NULL,
  crdb_region crdb_internal_region NOT NULL DEFAULT gateway_region()::crdb_internal_region,
  payload JSONB NOT NULL,
  PRIMARY KEY (job_id, crdb_region),
  INDEX platform_jobs_org_idx (org_id)
) LOCALITY REGIONAL BY ROW AS crdb_region;

CREATE TABLE IF NOT EXISTS job_assignments (
  job_id STRING NOT NULL,
  org_id STRING NOT NULL,
  crdb_region crdb_internal_region NOT NULL DEFAULT gateway_region()::crdb_internal_region,
  payload JSONB NOT NULL,
  PRIMARY KEY (job_id, crdb_region),
  INDEX job_assignments_org_idx (org_id)
) LOCALITY REGIONAL BY ROW AS crdb_region;

CREATE TABLE IF NOT EXISTS operator_presence (
  org_id STRING NOT NULL,
  principal_id STRING NOT NULL,
  crdb_region crdb_internal_region NOT NULL DEFAULT gateway_region()::crdb_internal_region,
  payload JSONB NOT NULL,
  PRIMARY KEY (org_id, principal_id, crdb_region)
) LOCALITY REGIONAL BY ROW AS crdb_region;

CREATE TABLE IF NOT EXISTS mesh_events (
  event_id STRING NOT NULL,
  org_id STRING NOT NULL,
  crdb_region crdb_internal_region NOT NULL DEFAULT gateway_region()::crdb_internal_region,
  payload JSONB NOT NULL,
  PRIMARY KEY (event_id, crdb_region),
  INDEX mesh_events_org_created_idx (org_id, event_id DESC)
) LOCALITY REGIONAL BY ROW AS crdb_region;

-- ---------------------------------------------------------------------------
-- Org-scoped tables (default regional; index org_id for tenant scans)
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS artifact_refs (
  ref_id STRING PRIMARY KEY,
  org_id STRING NOT NULL,
  payload JSONB NOT NULL,
  INDEX artifact_refs_org_idx (org_id)
);

CREATE TABLE IF NOT EXISTS usage_daily (
  org_id STRING NOT NULL,
  day STRING NOT NULL,
  payload JSONB NOT NULL,
  PRIMARY KEY (org_id, day)
);

CREATE TABLE IF NOT EXISTS billing_periods (
  org_id STRING NOT NULL,
  period STRING NOT NULL,
  payload JSONB NOT NULL,
  PRIMARY KEY (org_id, period)
);

CREATE TABLE IF NOT EXISTS org_policy_rules (
  rule_id STRING PRIMARY KEY,
  org_id STRING NOT NULL,
  payload JSONB NOT NULL,
  INDEX org_policy_rules_org_idx (org_id)
);

CREATE TABLE IF NOT EXISTS workflows (
  workflow_id STRING PRIMARY KEY,
  org_id STRING NOT NULL,
  payload JSONB NOT NULL,
  INDEX workflows_org_idx (org_id)
);

CREATE TABLE IF NOT EXISTS workflow_listings (
  listing_id STRING PRIMARY KEY,
  org_id STRING NOT NULL,
  payload JSONB NOT NULL
);

CREATE TABLE IF NOT EXISTS webhook_subscriptions (
  subscription_id STRING PRIMARY KEY,
  org_id STRING NOT NULL,
  payload JSONB NOT NULL,
  INDEX webhook_subscriptions_org_idx (org_id)
);

CREATE TABLE IF NOT EXISTS webhook_deliveries (
  delivery_id STRING PRIMARY KEY,
  org_id STRING NOT NULL,
  payload JSONB NOT NULL,
  INDEX webhook_deliveries_org_idx (org_id)
);

CREATE TABLE IF NOT EXISTS platform_ledger (
  entry_id STRING PRIMARY KEY,
  org_id STRING NOT NULL,
  payload JSONB NOT NULL,
  INDEX platform_ledger_org_idx (org_id)
);

CREATE TABLE IF NOT EXISTS autopilot_runs (
  run_id STRING PRIMARY KEY,
  org_id STRING NOT NULL,
  payload JSONB NOT NULL,
  INDEX autopilot_runs_org_idx (org_id)
);

CREATE TABLE IF NOT EXISTS on_call_schedules (
  rotation_id STRING PRIMARY KEY,
  org_id STRING NOT NULL,
  payload JSONB NOT NULL,
  INDEX on_call_schedules_org_idx (org_id)
);

CREATE TABLE IF NOT EXISTS handoff_bundles (
  bundle_id STRING PRIMARY KEY,
  org_id STRING NOT NULL,
  payload JSONB NOT NULL,
  INDEX handoff_bundles_org_idx (org_id)
);

-- Avoid SERIAL write hotspots on high-volume audit append.
CREATE TABLE IF NOT EXISTS audit_rows (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  org_id STRING NOT NULL,
  payload JSONB NOT NULL,
  INDEX audit_rows_org_id_idx (org_id, id DESC)
);

-- Proof / federation tables (global; low volume coordination)
CREATE TABLE IF NOT EXISTS proof_attestations (
  attestation_id STRING PRIMARY KEY,
  job_id STRING NOT NULL,
  payload JSONB NOT NULL,
  INDEX proof_attestations_job_idx (job_id)
) LOCALITY GLOBAL;

CREATE TABLE IF NOT EXISTS proof_runners (
  runner_id STRING PRIMARY KEY,
  payload JSONB NOT NULL
) LOCALITY GLOBAL;

CREATE TABLE IF NOT EXISTS proof_witnesses (
  witness_id STRING PRIMARY KEY,
  payload JSONB NOT NULL
) LOCALITY GLOBAL;

CREATE TABLE IF NOT EXISTS platform_peers (
  peer_id STRING PRIMARY KEY,
  payload JSONB NOT NULL
) LOCALITY GLOBAL;

CREATE TABLE IF NOT EXISTS listing_reviews (
  review_id STRING PRIMARY KEY,
  listing_id STRING NOT NULL,
  payload JSONB NOT NULL,
  INDEX listing_reviews_listing_idx (listing_id)
) LOCALITY GLOBAL;
