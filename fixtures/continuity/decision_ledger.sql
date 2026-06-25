-- Decision Ledger — constitutional DecisionObject store (SQLite)

CREATE TABLE IF NOT EXISTS decisions (
    id TEXT PRIMARY KEY,
    actor_id TEXT NOT NULL,
    identity_id TEXT NOT NULL,
    intent TEXT NOT NULL,
    type TEXT NOT NULL,
    evidence_refs_json TEXT NOT NULL,
    risk_profile_json TEXT NOT NULL,
    governance_basis_json TEXT NOT NULL,
    resource_plan_json TEXT NOT NULL,
    status TEXT NOT NULL,
    epoch INTEGER NOT NULL,
    tags_json TEXT NOT NULL,
    notes TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_decisions_status_epoch
    ON decisions (status, epoch);

CREATE INDEX IF NOT EXISTS idx_decisions_identity
    ON decisions (identity_id);

CREATE INDEX IF NOT EXISTS idx_decisions_actor
    ON decisions (actor_id);

CREATE TABLE IF NOT EXISTS decision_ledger (
    entry_id TEXT PRIMARY KEY,
    epoch INTEGER NOT NULL,
    entry_type TEXT NOT NULL,
    decision_id TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    prev_hash TEXT,
    hash TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_decision_ledger_decision
    ON decision_ledger (decision_id);

CREATE INDEX IF NOT EXISTS idx_decision_ledger_epoch
    ON decision_ledger (epoch);
