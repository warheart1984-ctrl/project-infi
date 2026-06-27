# /test — Nova Test Runner

1. Detect test framework from package.json / pyproject.toml / Makefile
2. Run all tests
3. For each failure: read the test + source, determine root cause, fix source (never delete tests)
4. Re-run — repeat up to 5 iterations
5. If still failing after 5 iterations: print a detailed diagnosis and stop

Output format:
- passed count
- failed count → fixing...
- fixes applied
- final pass status
