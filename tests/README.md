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

## Governance Test Harness

Session bootstrap (`tests/governance_bootstrap.py` + `tests/conftest.py`):

- `governance_bootstrap` session fixture — registers lanes, seeds membrane, admits memory gateway, issues synthetic `AAIS_TEST_ADMISSION_TOKEN`
- `governance_test_group_reset` module fixture — explicit registry reset between groups that call `module_governance.reset()`
- `pytest_collection_modifyitems` — runs phase/module/memory governance tests before `test_api.py`
- Cold-start admission — `AAIS_TEST_COLD_START=1` with `runtime_context=test_harness` only (never honored for live/operator runtime)

## Useful Commands

```bash
python -m pytest tests/test_api.py -q
python -m pytest tests/test_project_infi_law.py -q
python -m pytest tests/test_memory_board_enforcer.py tests/test_api.py::TestChatApi -q
```

## Read Next

1. [../src/README.md](../src/README.md)
2. [../docs/contracts/SEAM_LAW.md](../docs/contracts/SEAM_LAW.md)
3. [../docs/contracts/EXTERNAL_SUGGESTION_ADMISSION_RULE.md](../docs/contracts/EXTERNAL_SUGGESTION_ADMISSION_RULE.md)
