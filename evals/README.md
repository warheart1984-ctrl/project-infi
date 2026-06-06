# AAIS Evaluation Assets

This folder contains local evaluation prompts and scripts.

It supports runtime verification but does not define runtime truth.

## Main Files

- [`run_mode_eval.py`](./run_mode_eval.py)
  - local evaluation runner
- [`run_adapter_eval.py`](./run_adapter_eval.py)
  - base-vs-adapter eval with governed acceptance criteria (v2)
- [`mode_eval_prompts.json`](./mode_eval_prompts.json)
  - prompt set used by the local runner

## External Suggestion Admission

This folder inherits the project-wide external suggestion admission law.

Outside benchmark or evaluation proposals may be compared here, but they do not
become evaluation truth unless project law has filtered them and the admitted
form is documented.

## Read Next

1. [../training/README.md](../training/README.md)
2. [../tests/README.md](../tests/README.md)
3. [../docs/contracts/EXTERNAL_SUGGESTION_ADMISSION_RULE.md](../docs/contracts/EXTERNAL_SUGGESTION_ADMISSION_RULE.md)
