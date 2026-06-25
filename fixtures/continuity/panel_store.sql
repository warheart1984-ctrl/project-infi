-- Panel store — reflexive, steward, and perception evidence (SQLite)
-- Runtime also maintains legacy typed tables for backward compatibility.

CREATE TABLE IF NOT EXISTS panels (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    panel_type TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    steward_identity TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_panels_type ON panels(panel_type);
CREATE INDEX IF NOT EXISTS idx_panels_created ON panels(created_at);

CREATE TABLE IF NOT EXISTS reflexive_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    kind TEXT NOT NULL,
    epoch_id TEXT NOT NULL,
    intent_id TEXT,
    lineage_event_id TEXT NOT NULL,
    t5_ref_signal_hash TEXT NOT NULL,
    payload TEXT NOT NULL,
    timestamp TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS steward_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    kind TEXT NOT NULL,
    payload TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS perception_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    intent_id TEXT NOT NULL,
    epoch_id TEXT NOT NULL,
    inputs TEXT NOT NULL,
    outputs TEXT NOT NULL,
    confidence REAL NOT NULL,
    anomaly_score REAL NOT NULL
);
