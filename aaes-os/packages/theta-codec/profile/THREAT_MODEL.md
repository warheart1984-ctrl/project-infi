# Theta-BIP39 Encoding Profile v0.1 Threat Model

## Theta-Layer Ambiguity
Multi-glyph Theta entries can produce multiple digits. R1 prevents reverse encoding from selecting an index unless its forward expansion contains the requested digit.

## Non-Deterministic Seed Generation
Probabilistic or environment-dependent behavior could cause wallet divergence. D1 forbids randomness and probabilistic branching in the canonical path.

## Mapping Drift
Silent changes to mappings can change seeds for the same glyph string. Profile versioning and change control are required.

## Entropy Collisions
Different digit sequences can theoretically collide after hashing. SHA-256 preimage resistance is relied upon, and fuzzing checks structural Theta-layer collisions.

## Implementation Bugs
Incorrect expansion, Theta selection, or entropy computation can corrupt seed derivation. The invariant suite covers reverse correctness, digit-space invariants, fuzzing, and determinism.
