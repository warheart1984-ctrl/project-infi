# EvolveEngine Service

This folder contains the bounded evolution and search service code.

It is governed by the EvolveEngine contract and does not own Jarvis runtime
authority.

## Main Files

- [`main.py`](./main.py)
  - service entry surface
- [`service.py`](./service.py)
  - evolve job handling
- [`schemas.py`](./schemas.py)
  - service payload schemas

## External Suggestion Admission

This folder inherits the project-wide external suggestion admission law.

Outside mutation or search proposals may be compared here, but they do not
become EvolveEngine truth unless project law has filtered them and the admitted
form is documented.

## Read Next

1. [../docs/contracts/EVOLVE_ENGINE_CONTRACT.md](../docs/contracts/EVOLVE_ENGINE_CONTRACT.md)
2. [../docs/contracts/EXTERNAL_SUGGESTION_ADMISSION_RULE.md](../docs/contracts/EXTERNAL_SUGGESTION_ADMISSION_RULE.md)
3. [../src/README.md](../src/README.md)
