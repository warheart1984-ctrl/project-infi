# How To Implement Theta-BIP39 Profile v0.1

1. Load `manifest.json` and assert profile `Theta-BIP39-Encoding`, version
   `0.1`, and status `stable`.
2. Implement the canonical mappings from `reference_implementation.ts`.
3. Decode glyph strings by tokenizing on `|` and `.`.
4. Resolve glyphs to canonical Theta indices without fuzzy correction.
5. Expand Theta glyphs into base-14 digits.
6. Compute entropy with `SHA256(digits_to_bytes(digits))[:16]`.
7. Append BIP-39 checksum bits.
8. Split the result into 11-bit word indices.
9. Derive seed material with PBKDF2-HMAC-SHA512, 2048 rounds.
10. Verify every vector in `test_vectors.json`.
11. Verify every hash in `reproducibility_lock.json`.

Conformance requires passing the complete profile test suite. A partial
implementation may be useful for inspection, but it must not claim Profile v0.1
conformance.
