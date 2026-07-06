# Test Runner Skill

## Detect framework
| Signal | Runner |
|--------|--------|
| `vitest` in package.json | `npm test` / `npx vitest` |
| `jest` in package.json | `npm test` |
| `pytest` in pyproject.toml | `pytest -q` |
| `Makefile` with `test` target | `make test` |

## Fix loop
1. Run full suite — capture baseline
2. Fix one failure at a time in source (not tests)
3. Re-run affected tests, then full suite
4. Max 5 iterations; then report blockers
