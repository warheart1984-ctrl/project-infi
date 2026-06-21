-- Meaning Ledger — MIT-1 operator meaning tracking (SQLite)

CREATE TABLE IF NOT EXISTS meaning_records (
    id TEXT PRIMARY KEY,
    object_type TEXT NOT NULL,
    object_id TEXT NOT NULL,
    mu REAL NOT NULL,
    M_purp REAL NOT NULL,
    M_cons REAL NOT NULL,
    M_stab REAL NOT NULL,
    M_intent REAL NOT NULL,
    epoch INTEGER NOT NULL,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_meaning_records_object
    ON meaning_records(object_type, object_id);

CREATE INDEX IF NOT EXISTS idx_meaning_records_epoch
    ON meaning_records(epoch);

CREATE TABLE IF NOT EXISTS meaning_ledger (
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

CREATE INDEX IF NOT EXISTS idx_meaning_ledger_object
    ON meaning_ledger(object_type, object_id);

CREATE INDEX IF NOT EXISTS idx_meaning_ledger_epoch
    ON meaning_ledger(epoch);
