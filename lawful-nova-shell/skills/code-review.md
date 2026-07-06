# Code Review Skill

## Order of review
1. Security (secrets, auth, injection)
2. Correctness (logic, edge cases)
3. Tests (coverage, assertions)
4. Performance (hot paths only)
5. Style (naming, clarity)

## Severity
- **CRITICAL** — must fix before merge
- **HIGH** — should fix before merge
- **MEDIUM** — fix or track issue
- **LOW** — optional polish

## Output template
```
CRITICAL: <one line> — path:line
HIGH: ...
```
