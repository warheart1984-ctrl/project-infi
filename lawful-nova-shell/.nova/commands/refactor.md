# /refactor — Nova Refactor

Refactor the specified file or directory.

Rules:
- Preserve ALL existing behavior and public API surface
- Do not change function signatures unless explicitly requested
- Add docstrings / JSDoc where missing
- Split files over 300 lines into focused modules
- Run tests after each significant change and confirm they pass
