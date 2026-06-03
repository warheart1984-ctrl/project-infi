# Coding Organs V1 Proof

## Claims

| Claim | Label |
|-------|-------|
| Patchforge organ attests proposal_only | asserted |
| Patch verification organ attests apply_requires_review | asserted |
| Silent apply is not allowed | asserted |

## Reproduction

```bash
make patchforge-organ-gate change-scope-organ-gate patch-verification-organ-gate
python -m pytest tests/test_patchforge_organ.py tests/test_change_scope_organ.py tests/test_patch_verification_organ.py -q
```
