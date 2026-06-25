-- Generative Ledger — GIT-1 Lambda tracking (SQLite)

CREATE TABLE IF NOT EXISTS generative_records (
    id TEXT PRIMARY KEY,
    object_type TEXT NOT NULL,
    object_id TEXT NOT NULL,
    lambda REAL NOT NULL,
    G_recover REAL NOT NULL,
    G_cross REAL NOT NULL,
    G_intra REAL NOT NULL,
    G_trace REAL NOT NULL,
    epoch INTEGER NOT NULL,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_generative_records_object
    ON generative_records(object_type, object_id);

CREATE INDEX IF NOT EXISTS idx_generative_records_epoch
    ON generative_records(epoch);

CREATE TABLE IF NOT EXISTS git_ledger (
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

CREATE INDEX IF NOT EXISTS idx_git_ledger_object
    ON git_ledger(object_type, object_id);

CREATE INDEX IF NOT EXISTS idx_git_ledger_epoch
    ON git_ledger(epoch);
