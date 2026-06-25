-- Continuity OS vault: sovereign continuity proofs and seal records.

CREATE TABLE IF NOT EXISTS vault_packages (
  id TEXT PRIMARY KEY,
  chain_id TEXT NOT NULL,
  document TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_vault_packages_chain ON vault_packages(chain_id);

CREATE TABLE IF NOT EXISTS vault_entries (
  id TEXT PRIMARY KEY,
  chain_id TEXT NOT NULL,
  document TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_vault_entries_chain ON vault_entries(chain_id);

CREATE TABLE IF NOT EXISTS vault_seal_records (
  id TEXT PRIMARY KEY,
  chain_id TEXT NOT NULL,
  document TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_vault_seals_chain ON vault_seal_records(chain_id);

CREATE TABLE IF NOT EXISTS vault_lineage_proofs (
  id TEXT PRIMARY KEY,
  chain_id TEXT NOT NULL,
  document TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_vault_lineage_chain ON vault_lineage_proofs(chain_id);

CREATE TABLE IF NOT EXISTS vault_observer_reports (
  id TEXT PRIMARY KEY,
  mission_id TEXT NOT NULL,
  document TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS vault_mission_completions (
  id TEXT PRIMARY KEY,
  mission_id TEXT NOT NULL,
  document TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS vault_ceremony_completions (
  id TEXT PRIMARY KEY,
  mission_id TEXT NOT NULL,
  document TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS vault_trust_boundary_updates (
  id TEXT PRIMARY KEY,
  chain_id TEXT NOT NULL,
  document TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS vault_mission_dossiers (
  mission_id TEXT PRIMARY KEY,
  document TEXT NOT NULL,
  created_at TEXT NOT NULL
);
