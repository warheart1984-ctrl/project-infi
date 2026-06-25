-- Claim registry: canonical claims + explicit links to PEL evidence.
-- Applied by src/cori/claims/store.py (CLAIM_REGISTRY_PATH / data/claim_registry.sqlite3).

-- Core claim table: one row per canonical claim
CREATE TABLE IF NOT EXISTS claims (
  id TEXT PRIMARY KEY,                 -- e.g. CLAIM-<uuid>
  kind TEXT NOT NULL,                  -- stewardship|ownership|economic|governance|attribution|other
  summary TEXT NOT NULL,               -- human-readable one-line description
  description TEXT,                    -- longer explanation
  subject_id TEXT,                     -- what the claim is about (asset id, repo, org, etc.)
  subject_type TEXT,                   -- asset|repo|org|person|system|other
  created_at TEXT NOT NULL,            -- ISO8601
  created_by TEXT NOT NULL,            -- actor/steward id
  status TEXT NOT NULL DEFAULT 'draft',-- draft|active|revoked|superseded
  tier TEXT,                           -- T1|T2|T3 or null
  notes TEXT
);

CREATE INDEX IF NOT EXISTS idx_claims_kind ON claims(kind);
CREATE INDEX IF NOT EXISTS idx_claims_subject ON claims(subject_id, subject_type);
CREATE INDEX IF NOT EXISTS idx_claims_status ON claims(status);

-- Link table: claims ↔ PEL evidence
CREATE TABLE IF NOT EXISTS claim_evidence_links (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  claim_id TEXT NOT NULL,
  pel_id TEXT NOT NULL,
  relation TEXT NOT NULL,              -- supports|refutes|context|derived_from
  strength TEXT NOT NULL,              -- primary|secondary|inferred
  created_at TEXT NOT NULL,
  created_by TEXT NOT NULL,
  FOREIGN KEY (claim_id) REFERENCES claims(id),
  -- pel_id refers into pel_records.id (no FK here to keep DBs loosely coupled)
  UNIQUE (claim_id, pel_id, relation, strength)
);

CREATE INDEX IF NOT EXISTS idx_claim_evidence_claim ON claim_evidence_links(claim_id);
CREATE INDEX IF NOT EXISTS idx_claim_evidence_pel ON claim_evidence_links(pel_id);
