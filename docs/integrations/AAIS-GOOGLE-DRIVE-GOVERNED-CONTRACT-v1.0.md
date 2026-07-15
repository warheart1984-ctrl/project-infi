# AAIS–Google Drive Governed Integration Contract v1.0

Status: Normative  
Version: 1.0  
Owner: AAIS Governance  
Dependencies: CEIP temporal semantics; CKCA evidence requirements  
Supersedes: None

The key words MUST, MUST NOT, SHOULD, SHOULD NOT, and MAY are to be interpreted as described by RFC 2119.

## Contract

Every Google Drive authorization, vault action, and file action MUST bind an AAIS actor, organization, and `google-drive` provider. Anonymous operations are prohibited. OAuth is separate from identity sign-in, uses offline consent, and is limited to `openid email profile` plus `drive.file`. ID tokens MUST be validated for signature, issuer, audience, and expiry.

Refresh tokens MUST be encrypted with AES-256-GCM using a per-user/organization derived key. Access tokens MUST NOT be persisted. Store, load, rotate, and revoke actions MUST emit evidence containing a non-secret token identifier. Disconnect MUST revoke consent at Google and prevent subsequent use.

The governed client supports list, search, fetch/export, upload, and update. Each successful operation MUST append a CEIP event and canonical evidence receipt before its result is accepted. Receipts use `ceip-jcs-nfc-v1`, SHA-256, RFC3339 time, a half-open temporal interval, and a lineage predecessor. Repeated file operations form a predecessor chain.

CLI commands `aais auth google-drive`, `aais drive ls`, `aais drive search`, `aais drive fetch`, `aais drive upload`, `aais drive update`, and `aais conformance drive --vector v1_0` MUST use the governed API and MUST NOT bypass evidence recording.

## Halt semantics

- Missing actor, organization, or vault binding: `HALT:AUTHORITY_ERROR`
- Evidence append failure: `HALT:EVIDENCE_ERROR`
- Non-canonicalizable evidence: `HALT:CANONICALIZATION_ERROR`

An operation with any of these outcomes is not valid constitutional evidence.

## CEIP/CKCA binding

Drive receipts are governed inputs to CRE; Drive-derived objects enter CKL with temporal lineage; CCC preserves revision continuity; CIC requires deterministic evidence-grounded inference; and MWCAM treats Google Drive as an external authority world.
