# /review — Nova Code Review

Review the current staged diff or specified file/directory.

## Checklist
- Security: hardcoded secrets, injection risks, missing auth checks
- Performance: N+1 queries, blocking async calls, memory leaks
- Tests: missing coverage, flaky patterns, edge cases
- Clarity: long functions, unclear names, dead code

## Output
- CRITICAL: issue — file:line
- HIGH: issue — file:line
- MEDIUM: issue — file:line
- LOW: issue — file:line

End with: "X issues found (Y critical, Z high, ...)"
