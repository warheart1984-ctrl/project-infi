-- Structural Ledger — SIT-1 Sigma tracking (SQLite)

CREATE TABLE IF NOT EXISTS structural_records (
    id TEXT PRIMARY KEY,
    object_type TEXT NOT NULL,
    object_id TEXT NOT NULL,
    sigma REAL NOT NULL,
    S_equiv REAL NOT NULL,
    S_indep REAL NOT NULL,
    S_recover REAL NOT NULL,
    S_trace REAL NOT NULL,
    epoch INTEGER NOT NULL,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_structural_records_object
    ON structural_records(object_type, object_id);

CREATE INDEX IF NOT EXISTS idx_structural_records_epoch
    ON structural_records(epoch);

CREATE TABLE IF NOT EXISTS sit_ledger (
    entry_id TEXT PRIMARY KEY,
    epoch INTEGER NOT NULL,
    entry_type TEXT NOT NULL,
    object_type TEXT NOT NULL,
    object_id TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    prev_hash TEXT,
    hash TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_sit_ledger_object
    ON sit_ledger(object_type, object_id);

CREATE INDEX IF NOT EXISTS idx_sit_ledger_epoch
    ON sit_ledger(epoch);
