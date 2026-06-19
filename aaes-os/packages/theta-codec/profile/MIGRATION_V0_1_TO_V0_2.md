# Theta-BIP39 Encoding

## Profile v0.1 to v0.2 Migration Guide

This document describes the required steps, checks, and governance actions for migrating from Profile v0.1 to Profile v0.2.

## 1. When A Version Bump Is Required

A new profile version is required if any of the following change:

- `theta_map`
- `digit_map`
- `digit_to_theta_indices`
- `digits_to_entropy_128`
- Theta-to-digit forward expansion rules
- Entropy hashing or truncation rules
- BIP-39 bit or word index pipeline

If none of these change, the profile version must remain v0.1.

## 2. Migration Steps

1. Fork Profile v0.1 into a new profile directory or branch.
2. Apply only the proposed changes required for the new profile.
3. Document each change in a Profile Change Proposal.
4. Rebuild `theta_to_digits`, `digit_to_theta_indices`, and deterministic Theta choreography.
5. Recompute canonical test vectors: glyphs to digits, digits to entropy, entropy to BIP-39 indices.
6. Run the full invariant suite:
   - Theta reverse correctness (R1)
   - Digit-space invariants
   - Theta round-trip entropy fuzzer
   - BIP-39 determinism (D1)
7. Update the profile manifest.
8. Publish migration notes describing compatibility impact.

## 3. Backward Compatibility

Profile v0.2 is not required to be backward-compatible with v0.1.

If v0.2 changes the mapping from glyph strings to seeds, this must be explicitly documented. Profile v0.1 must remain available for decoding legacy data.

## 4. Approval

A migration to v0.2 requires:

- One Profile Change Proposal
- Two reviewers
- Full test suite passing
- Manifest and README updates

Status: draft
