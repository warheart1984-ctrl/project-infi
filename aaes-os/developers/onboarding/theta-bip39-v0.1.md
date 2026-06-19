# Developer Onboarding Guide
## Theta-BIP39 Encoding Profile v0.1

This guide helps external implementers build Theta-BIP39 Encoding Profile v0.1
in any language, then verify conformance against the AAES OS standard.

## 1. What You Need To Implement

You must implement:

1. Theta-layer forward decoding.
2. Theta-layer reverse mapping.
3. Digit sequence construction.
4. Entropy function: SHA-256 truncated to 128 bits.
5. BIP-39 bit construction: entropy plus checksum.
6. 11-bit index extraction.
7. PBKDF2-HMAC-SHA512 seed derivation.

## 2. Required Invariants

### R1 - Theta-Reverse Correctness

`reverse(d)` must select only Theta indices whose forward expansion contains
`d`.

### D1 - BIP-39 Determinism

The entire canonical pipeline must be deterministic.

## 3. Required Files

Use these files from `standards/theta-bip39/v0.1`:

- `manifest.json`
- `theta-bip39-profile-v0.1-spec.md`
- `reference_implementation.ts`
- `test_runner.ts`
- `test_vectors.json`
- `reproducibility_lock.json`
- `reproducibility_harness.ts`

AAES OS uses TypeScript as the canonical reference implementation. Other
language implementations must match its behavior.

## 4. Implementation Steps

1. Implement glyph-to-digit expansion.
2. Implement Theta-index-to-glyph mapping.
3. Implement `reverse(d)` using the derived valid reverse set.
4. Implement base-14 digit-to-bytes conversion.
5. Implement the SHA-256 entropy function.
6. Implement BIP-39 checksum logic.
7. Implement 11-bit index extraction.
8. Implement PBKDF2-HMAC-SHA512 with 2048 rounds.
9. Run the official test vectors.
10. Run the reproducibility harness.

## 5. Conformance Requirements

Your implementation is conformant if:

- all test vectors match
- R1 and D1 pass
- the reproducibility harness passes
- the Profile v0.1 Conformance Header is included

## 6. Support And Change Proposals

Open an issue or submit a Profile Change Proposal for proposed changes. Do not
change profile-critical behavior and still claim v0.1 conformance.
