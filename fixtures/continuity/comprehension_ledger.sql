-- Comprehension Ledger — CIT-1 / CIT-2 operator comprehension tracking (SQLite)

CREATE TABLE IF NOT EXISTS comprehension_records (
    id TEXT PRIMARY KEY,
    object_type TEXT NOT NULL,
    object_id TEXT NOT NULL,
    chi REAL NOT NULL,
    C_loc REAL NOT NULL,
    C_clr REAL NOT NULL,
    C_cons REAL NOT NULL,
    C_link REAL NOT NULL,
    epoch INTEGER NOT NULL,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_comprehension_records_object
    ON comprehension_records(object_type, object_id);

CREATE INDEX IF NOT EXISTS idx_comprehension_records_epoch
    ON comprehension_records(epoch);

CREATE TABLE IF NOT EXISTS comprehension_ledger (
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

CREATE INDEX IF NOT EXISTS idx_comprehension_ledger_object
    ON comprehension_ledger(object_type, object_id);

CREATE INDEX IF NOT EXISTS idx_comprehension_ledger_epoch
    ON comprehension_ledger(epoch);
