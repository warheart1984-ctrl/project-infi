# Trust Bundle Template

Use this template for significant AI-driven fix/test/release claims.
Normative schema is defined in `docs/TRUST_BUNDLE_SPEC.md`.

```text
claim_label: asserted
why_short: |
  <line 1>
  <line 2>
proof_links:
  - <path-or-url-to-proof-artifact>
none_yet: false
override_command: <single-command-human-override-or-none>
override_breaks_blueprint: false
debt_ticket_ref: none
created_at_utc: 2026-05-27T20:40:00Z
updated_at_utc: 2026-05-27T20:40:00Z
author: <human-or-agent-identity>
context: <issue-pr-task-context>
```

Checklist:

- `claim_label` is one of `asserted`, `proven`, `rejected`.
- `why_short` is at most 5 lines.
- Use exactly one proof mode:
  - evidence mode: non-empty `proof_links` with `none_yet: false`, or
  - pending mode: `none_yet: true` (typically with `claim_label: asserted`).
- `override_command` is present (or `none`).
- If `override_breaks_blueprint: true`, `debt_ticket_ref` is a real ticket reference.
