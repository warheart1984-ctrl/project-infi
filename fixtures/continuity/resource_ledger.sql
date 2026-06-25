-- Resource Ledger — constitutional ResourceObject store (SQLite)

CREATE TABLE IF NOT EXISTS resources (
    id TEXT PRIMARY KEY,
    type TEXT NOT NULL,
    label TEXT,
    quantity_total REAL NOT NULL,
    quantity_allocated REAL NOT NULL,
    quantity_unit TEXT NOT NULL,
    constraints_json TEXT NOT NULL,
    allocations_json TEXT NOT NULL,
    status TEXT NOT NULL,
    epoch INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_resources_type ON resources (type);
CREATE INDEX IF NOT EXISTS idx_resources_status ON resources (status);
