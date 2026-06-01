# ForgeEval Service

This folder contains the bounded evaluation service used by Forge-facing flows.

It is governed by the ForgeEval contract and does not own Jarvis runtime
authority.

## Main Files

- [`main.py`](./main.py)
  - service entry surface
- [`service.py`](./service.py)
  - evaluator service logic
- [`schemas.py`](./schemas.py)
  - service payload schemas

## External Suggestion Admission

This folder inherits the project-wide external suggestion admission law.

Outside evaluation proposals may be compared here, but they do not become
ForgeEval truth unless project law has filtered them and the admitted form is
documented.

## Read Next

1. [../docs/contracts/FORGEEVAL_CONTRACT.md](../docs/contracts/FORGEEVAL_CONTRACT.md)
2. [../docs/contracts/EXTERNAL_SUGGESTION_ADMISSION_RULE.md](../docs/contracts/EXTERNAL_SUGGESTION_ADMISSION_RULE.md)
3. [../src/README.md](../src/README.md)
