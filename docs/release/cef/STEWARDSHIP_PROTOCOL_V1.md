# Stewardship Protocol v1.0

**Status:** Specified — CEF v1.0  
**Parent:** [CEF_V1_CHARTER.md](./CEF_V1_CHARTER.md) Article VI

## 1. Purpose

Stewardship ensures that certificates remain trustworthy, replayable, auditable, and aligned with constitutional invariants.

## 2. Stewardship States

| State | Meaning |
| --- | --- |
| `unpromoted` | Certificate in DRAFT / HOLD |
| `active` | Certificate promoted and valid |
| `renewal_pending` | Certificate nearing expiration / re-verification due |
| `revoked` | Certificate invalidated |
| `historical` | Certificate preserved for replay / audit |

Allowed transitions:

```text
unpromoted → active
active → renewal_pending → active
active → revoked → historical
active → historical
renewal_pending → revoked → historical
unpromoted → historical   (abandoned draft archival)
```

## 3. Stewardship Responsibilities

### Monitoring

- Runtime health (OEL)
- Policy compliance
- Security posture

### Renewal

- Re-verification
- Re-promotion
- Updated evidence

### Revocation

- MUST produce revocation evidence
- MUST be signed by authority

### Replay

- Deterministic reconstruction of certificate lineage

### Audit

- Disclosure rules
- Evidence chain visibility
- Governance trace

## 4. Stewardship Invariants

1. No certificate may remain active without valid evidence.
2. No certificate may be revoked without evidence.
3. All certificates must remain replayable.
4. All certificates must remain auditable.
