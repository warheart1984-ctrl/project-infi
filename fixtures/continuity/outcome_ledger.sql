-- Outcome Ledger — constitutional OutcomeObject store (SQLite)

CREATE TABLE IF NOT EXISTS outcomes (
    id TEXT PRIMARY KEY,
    decision_id TEXT NOT NULL,
    expected_json TEXT NOT NULL,
    observed_json TEXT NOT NULL,
    variance_json TEXT NOT NULL,
    lessons_json TEXT NOT NULL,
    epoch INTEGER NOT NULL,
    status TEXT NOT NULL,
    timestamp TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_outcomes_decision
    ON outcomes (decision_id);

CREATE INDEX IF NOT EXISTS idx_outcomes_epoch
    ON outcomes (epoch);

CREATE INDEX IF NOT EXISTS idx_outcomes_status
    ON outcomes (status);

CREATE TABLE IF NOT EXISTS outcome_ledger (
    entry_id TEXT PRIMARY KEY,
    epoch INTEGER NOT NULL,
    entry_type TEXT NOT NULL,
    outcome_id TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    prev_hash TEXT,
    hash TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_outcome_ledger_outcome
    ON outcome_ledger (outcome_id);

CREATE INDEX IF NOT EXISTS idx_outcome_ledger_epoch
    ON outcome_ledger (epoch);
