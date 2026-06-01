# Trust Bundle Specification

Status: Normative. This specification operationalizes Doctrine XI in `META_ARCHITECT_LAWBOOK.md` and `REPO_PROOF_LAW.md`.

## 1. Scope

A Trust Bundle is required for every significant AI-driven fix, test, or release contribution claim.
Each significant claim MUST be represented by one Trust Bundle record.

## 2. Claim Taxonomy Alignment (Required)

`claim_label` MUST be one of:

- `asserted`: insufficient evidence; not admissible for acceptance.
- `proven`: evidence complete and traceable; admissible for acceptance.
- `rejected`: disproven, invalidated, or evidence-incomplete after review.

## 3. Required Fields (Normative Schema)

Trust Bundle records MUST include the following keys:

- `claim_label` (required, enum)
- `why_short` (required, 1-5 lines max)
- `proof_links` or `none_yet` (required, exactly one mode)
- `override_command` (required, one-command human override or `none`)
- `debt_ticket_ref` (conditionally required)
- `created_at_utc` (required, ISO-8601 UTC)
- `updated_at_utc` (required, ISO-8601 UTC)
- `author` (required, human/agent identity)
- `context` (required, short issue/PR/task context)

Conditional field rule:

- `debt_ticket_ref` is REQUIRED when `override_breaks_blueprint: true`.
- `debt_ticket_ref` MAY be `none` when `override_breaks_blueprint: false`.

## 4. Canonical Record Format

```text
claim_label: asserted|proven|rejected
why_short: |
  line 1
  line 2
proof_links:
  - path/or/url
  - path/or/url
none_yet: false
override_command: <single command or "none">
override_breaks_blueprint: true|false
debt_ticket_ref: <ticket id or "none">
created_at_utc: 2026-05-27T20:40:00Z
updated_at_utc: 2026-05-27T20:40:00Z
author: <name-or-agent-id>
context: <short context string>
```

Notes:

- Use `none_yet: true` only when no proof artifacts exist yet and `claim_label` is `asserted`.
- `proof_links` MUST be a non-empty list when `none_yet: false`.
- `why_short` SHOULD state rationale, assumptions, and uncertainty bounds in plain language.

## 5. Validation Rules

1. `claim_label` MUST match the required taxonomy values.
2. `why_short` MUST be present and no more than 5 non-empty lines.
3. Exactly one proof mode is allowed:
   - Mode A: `proof_links` with one or more links and `none_yet: false`.
   - Mode B: `none_yet: true` and empty/absent `proof_links`.
4. `override_command` MUST be present (`none` is allowed when not applicable).
5. If `override_breaks_blueprint: true`, `debt_ticket_ref` MUST NOT be `none`.
6. `created_at_utc` and `updated_at_utc` MUST be valid UTC timestamps.
7. `author` and `context` MUST be non-empty.

## 6. Validation Examples

### Pass Example (Proven)

```text
claim_label: proven
why_short: |
  Governance validator now checks Trust Bundle schema in CI.
  This enforces Doctrine XI one-click verification for significant AI-driven changes.
proof_links:
  - docs/trust_bundles/2026-05-27-doctrine-xi-governance-integration.md
none_yet: false
override_command: none
override_breaks_blueprint: false
debt_ticket_ref: none
created_at_utc: 2026-05-27T20:40:00Z
updated_at_utc: 2026-05-27T20:40:00Z
author: codex-5.3
context: doctrine-xi-governance-integration
```

### Pass Example (Asserted, No Proof Yet)

```text
claim_label: asserted
why_short: |
  Initial draft is prepared for review.
  Validation evidence will be attached after CI run.
none_yet: true
override_command: git restore --source=HEAD -- docs/TRUST_BUNDLE_SPEC.md
override_breaks_blueprint: false
debt_ticket_ref: none
created_at_utc: 2026-05-27T20:40:00Z
updated_at_utc: 2026-05-27T20:40:00Z
author: contributor@example
context: trust-bundle-spec-draft
```

### Fail Example (Invalid)

```text
claim_label: complete
why_short: |
  Done.
proof_links:
none_yet: false
override_command:
override_breaks_blueprint: true
debt_ticket_ref: none
created_at_utc: 05/27/2026
updated_at_utc:
author:
context:
```

Reasons this fails:

- Invalid `claim_label` value (`complete`).
- Empty `proof_links` while `none_yet` is false.
- Missing `override_command`.
- Blueprint-breaking override without debt ticket reference.
- Invalid/missing timestamps and identity/context fields.

## 7. Storage and Discovery

- Recommended location: `docs/trust_bundles/`.
- Contributors SHOULD start from `templates/TRUST_BUNDLE_TEMPLATE.md`.
- CI governance checks consume Trust Bundles from the expected location and enforce schema requirements for significant AI-driven changes.
