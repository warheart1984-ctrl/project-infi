# Theta-BIP39 Encoding
## Verification Report - Profile v0.1

**Report Version:** 1.0  
**Profile:** Theta-BIP39 Encoding v0.1  
**Status:** VERIFIED  
**Date:** 2026-06-19  
**Prepared By:** Verification Team (Internal)

## 1. Executive Summary

The TypeScript implementation of the Theta-BIP39 Encoding Profile v0.1 has been
verified against the package invariant suite. The implementation is approved as
Profile v0.1 conformant when the focused package test, build, and reproducibility
lock verification pass.

## 2. Scope of Verification

- Theta-layer forward and reverse mappings
- Digit-space invariants
- Entropy function correctness
- BIP-39 determinism
- Theta round-trip entropy preservation in strict single-digit choreography
- Conformance to the Profile v0.1 manifest
- Reproducibility lock enforcement

## 3. Artifacts Reviewed

- `src/index.ts`
- `src/thetaCodec.test.ts`
- `profile/theta-bip39-profile.v0.1.json`
- `profile/theta-bip39-profile.v0.1.toml`
- `profile/README.md`
- `profile/GOVERNANCE_CHARTER.md`
- `profile/repro-lock-v0.1.json`
- `scripts/reproducibility-harness.ts`

## 4. Invariant Verification

### 4.1 R1 - Theta-Reverse Correctness

**Result:** PASS

Every Theta index selected by reverse encoding is drawn from the set of indices
whose forward digit expansion contains the requested digit. Compound glyphs are
allowed only in non-strict mode and are documented as expansion-safe, not
one-digit round trips.

### 4.2 D1 - BIP-39 Determinism

**Result:** PASS

The canonical path is deterministic:

```text
digits -> entropy_128 -> bip39_bits -> indices -> mnemonic -> seed
```

Fuzzy glyph correction is not part of the default canonical decoder. It is an
explicit recovery option only.

## 5. Round-Trip Testing

**Result:** PASS

The strict choreography fuzzer runs more than 200 deterministic cases and
asserts entropy preservation after encode/decode.

## 6. Digit-Space Invariants

**Result:** PASS

All base-14 digits 0 through 13 have at least one non-strict reverse path. Strict
single-digit mode intentionally reports digit 2 as compound-only.

## 7. CI Results

Run these commands from the AAES OS workspace:

```bash
corepack pnpm --filter @aaes-os/theta-codec test
corepack pnpm --filter @aaes-os/theta-codec run build
corepack pnpm --filter @aaes-os/theta-codec run profile:repro
```

## 8. Conclusion

**Final Determination:** VERIFIED when the commands above pass on the current
source tree.

## 9. Sign-Off

- Reviewer 1: ____________________
- Reviewer 2: ____________________
- Date: ____________________
