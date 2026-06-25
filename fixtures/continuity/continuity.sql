-- Continuity store — identity snapshots and governed spine events (SQLite)

CREATE TABLE IF NOT EXISTS identity_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    steward_identity TEXT NOT NULL,
    snapshot_json TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS continuity_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_continuity_events_type ON continuity_events(event_type);
CREATE INDEX IF NOT EXISTS idx_identity_snapshots_steward ON identity_snapshots(steward_identity);

CREATE TABLE IF NOT EXISTS assets (
    id TEXT PRIMARY KEY,
    asset_type TEXT NOT NULL,
    metadata_json TEXT NOT NULL,
    steward_identity TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_assets_steward ON assets(steward_identity);

CREATE TABLE IF NOT EXISTS invariant_status (
    invariant_id TEXT PRIMARY KEY,
    status TEXT NOT NULL,
    last_run_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    detail_json TEXT NOT NULL DEFAULT '{}'
);
