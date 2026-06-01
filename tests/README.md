# AAIS Test Suite

This folder contains the backend verification suite for AAIS.

It proves runtime behavior but does not replace runtime ownership.

## Owns

- backend pytest coverage
- seam regressions
- law enforcement regressions
- operator, memory, routing, provider, and workflow verification

## Does Not Own

- frontend Vitest coverage in [`../frontend/`](../frontend/)
- packaged launcher behavior in [`../aais/`](../aais/)

## External Suggestion Admission

This folder inherits the project-wide external suggestion admission law.

Outside testing ideas may be compared or pressure-tested here, but they do not
become canonical verification truth unless project law has filtered them and
the admitted form is documented.

## Useful Commands

```bash
python -m pytest tests/test_api.py -q
python -m pytest tests/test_project_infi_law.py -q
```

## Read Next

1. [../src/README.md](../src/README.md)
2. [../docs/contracts/SEAM_LAW.md](../docs/contracts/SEAM_LAW.md)
3. [../docs/contracts/EXTERNAL_SUGGESTION_ADMISSION_RULE.md](../docs/contracts/EXTERNAL_SUGGESTION_ADMISSION_RULE.md)
