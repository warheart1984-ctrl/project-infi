-- Evidence Ledger — proof objects for EIT-1 (SQLite)

CREATE TABLE IF NOT EXISTS evidence_records (
    evidence_id TEXT PRIMARY KEY,
    evidence_hash TEXT NOT NULL,
    evidence_type TEXT NOT NULL,
    source_lineage TEXT NOT NULL,
    source_epoch INTEGER NOT NULL,
    validation_method TEXT NOT NULL,
    confidence REAL NOT NULL,

    dependencies TEXT,
    trace_links TEXT,
    canonical_hash TEXT
);

CREATE TABLE IF NOT EXISTS evidence_ledger (
    entry_id TEXT PRIMARY KEY,
    prev_hash TEXT,
    timestamp TEXT NOT NULL,
    epoch INTEGER NOT NULL,
    entry_type TEXT NOT NULL,
    evidence_id TEXT NOT NULL,
    evidence_hash TEXT NOT NULL,
    payload TEXT,
    signed_by TEXT NOT NULL,
    signature TEXT NOT NULL,
    FOREIGN KEY(evidence_id) REFERENCES evidence_records(evidence_id)
);

CREATE INDEX IF NOT EXISTS idx_evidence_ledger_evidence_id
    ON evidence_ledger(evidence_id);

CREATE INDEX IF NOT EXISTS idx_evidence_ledger_epoch
    ON evidence_ledger(epoch);
