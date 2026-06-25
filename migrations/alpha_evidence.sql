-- Alpha evidence cycle artifacts (PELRecord, Claim, VerificationRecord as JSON documents).

CREATE TABLE IF NOT EXISTS alpha_pel_records (
  id TEXT PRIMARY KEY,
  audit_id TEXT,
  document TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_alpha_pel_audit ON alpha_pel_records(audit_id);

CREATE TABLE IF NOT EXISTS alpha_claims (
  id TEXT PRIMARY KEY,
  document TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS alpha_verifications (
  id TEXT PRIMARY KEY,
  claim_id TEXT NOT NULL,
  pel_record_id TEXT NOT NULL,
  document TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_alpha_verif_claim ON alpha_verifications(claim_id);
CREATE INDEX IF NOT EXISTS idx_alpha_verif_pel ON alpha_verifications(pel_record_id);
