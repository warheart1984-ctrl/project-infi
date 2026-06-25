-- RA-COS threshold registry + recalibration ledger (SQLite)

CREATE TABLE IF NOT EXISTS thresholds (
    id TEXT PRIMARY KEY,
    snapshot_json TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS threshold_versions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    threshold_id TEXT NOT NULL,
    version INTEGER NOT NULL,
    snapshot_json TEXT NOT NULL,
    delta_rationale TEXT NOT NULL DEFAULT '',
    recalibration_event_id TEXT,
    created_at TEXT NOT NULL,
    created_by TEXT NOT NULL,
    UNIQUE(threshold_id, version)
);

CREATE INDEX IF NOT EXISTS idx_threshold_versions_threshold
    ON threshold_versions(threshold_id);

CREATE TABLE IF NOT EXISTS recalibration_events (
    event_id TEXT PRIMARY KEY,
    decision TEXT NOT NULL,
    threshold_id TEXT,
    event_json TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_recalibration_events_decision
    ON recalibration_events(decision);

CREATE INDEX IF NOT EXISTS idx_recalibration_events_threshold
    ON recalibration_events(threshold_id);

-- Stub for interpretive stewardship (no writes in demo quarter)
CREATE TABLE IF NOT EXISTS observation_patterns (
    id TEXT PRIMARY KEY,
    pattern_json TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
