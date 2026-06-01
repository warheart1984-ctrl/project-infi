# UGR LLM Provider Execution Proof

Claim status: **asserted** (local verification)

## Verification

```bash
make ugr-llm-provider-gate
```

## Artifacts

- `src/ugr/governed_llm_executor.py`
- `src/ugr/llm_lane.py` (optional execution via `UGR_LLM_EXECUTE=1` or `force_execute` in tests)
- `tests/test_ugr_governed_llm_executor.py`
