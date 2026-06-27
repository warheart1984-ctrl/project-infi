# Git Workflow Skill

## Conventional commits
- `feat:` new feature
- `fix:` bug fix
- `chore:` tooling, deps
- `docs:` documentation only
- `refactor:` behavior-preserving restructure
- `test:` tests only
- `ci:` pipeline changes

## Branch flow
1. Branch from `main`: `feat/short-description`
2. Commit in small logical chunks
3. Open PR with What / Why / How to test
4. Never push directly to `main`

## gh CLI
```bash
gh pr create --title "feat(scope): summary" --body "..."
gh pr checks
gh issue list
```
