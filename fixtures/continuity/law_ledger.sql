-- Law Ledger — sovereign substrate law lifecycle (SQLite)

CREATE TABLE IF NOT EXISTS law_records (
    law_id TEXT PRIMARY KEY,
    version TEXT NOT NULL,
    law_hash TEXT NOT NULL,
    spec_ref TEXT NOT NULL,
    status TEXT NOT NULL,
    created_at_epoch INTEGER NOT NULL,
    introduced_by TEXT NOT NULL,

    current_fitness REAL,
    admit_threshold REAL,
    reject_threshold REAL,

    domains TEXT,
    dependencies TEXT,
    conflicts TEXT,
    supersedes TEXT
);

CREATE TABLE IF NOT EXISTS law_fitness_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    law_id TEXT NOT NULL,
    epoch INTEGER NOT NULL,
    fitness REAL NOT NULL,
    sample_size INTEGER NOT NULL,
    notes TEXT,
    FOREIGN KEY(law_id) REFERENCES law_records(law_id)
);

CREATE TABLE IF NOT EXISTS law_ledger (
    entry_id TEXT PRIMARY KEY,
    prev_hash TEXT,
    timestamp TEXT NOT NULL,
    epoch INTEGER NOT NULL,
    entry_type TEXT NOT NULL,
    law_id TEXT NOT NULL,
    law_hash TEXT NOT NULL,
    payload TEXT,
    signed_by TEXT NOT NULL,
    signature TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_law_fitness_history_law_epoch
    ON law_fitness_history(law_id, epoch);

CREATE INDEX IF NOT EXISTS idx_law_ledger_law_id
    ON law_ledger(law_id);

CREATE INDEX IF NOT EXISTS idx_law_ledger_epoch
    ON law_ledger(epoch);
