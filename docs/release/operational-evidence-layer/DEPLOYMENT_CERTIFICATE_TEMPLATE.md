# Deployment Certificate Template

Use this markdown projection for operator review. Machine form MUST also exist as JSON conforming to `deployment-certificate.schema.json`, backed by an Evidence Record conforming to `operational-evidence-record.schema.json`.

---

## Deployment Certificate

| Field | Value |
| --- | --- |
| **Deployment Certificate** | `<CERTIFICATE-ID>` |
| **Version** | `<semver or baseline id>` |
| **Commit SHA** | `<git sha>` |
| **Image Digest** | ☐ pending / ✓ pass / ✗ fail |
| **SBOM Verified** | ☐ pending / ✓ pass / ✗ fail / ⚠ waived |
| **Conformance Tests** | `<passed>/<total>` |
| **Security Scan** | PASS / FAIL / PENDING |
| **Policy Validation** | PASS / FAIL / PENDING |
| **Runtime Health** | healthy / degraded / unhealthy / pending |
| **Promotion Authority** | `<authority name>` |
| **Promotion Decision** | promote / hold / deny / pending |
| **Approval Signature** | signed / unsigned / pending — `<signer>` |
| **Timestamp** | `<ISO-8601>` |
| **Overall Status** | CERTIFIED / CONDITIONAL / DENIED / DRAFT |
| **Proof Surface Level** | P0–P5 |

### Truth boundary

`<what this certificate does not claim>`

### Challenge surface

- `<condition that would invalidate the certificate>`

### Evidence record reference

`<path or recordId>`

---

**Rule:** Do not present a green certificate when any required gate is `pending` unless Overall Status is explicitly `DRAFT` or `CONDITIONAL` with failing/pending gates listed.
