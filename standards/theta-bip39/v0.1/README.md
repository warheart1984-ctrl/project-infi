# Theta-BIP39 Encoding - Profile v0.1

## Overview

Profile v0.1 defines a deterministic pipeline for converting symbolic Theta-layer glyph strings into BIP-39-compatible entropy and seeds.

The profile guarantees:

- Theta-reverse encoding is structurally correct through invariant R1.
- BIP-39 derivation is deterministic and environment-independent through invariant D1.
- The Theta layer, digit mapping, and entropy function are version-locked.

This profile is stable. Any modification to core mappings or entropy rules requires a new profile version.

## Pipeline

```text
glyphs -> Theta indices -> digits -> entropy_128 -> bip39_bits -> indices -> seed
```

All canonical steps are pure functions. No randomness or probabilistic branching is permitted in the canonical BIP-39 path.

## Invariants

### R1 - Theta-Reverse Correctness

For every digit `d` and every Theta index `t` chosen during reverse encoding:

```text
d in forward_digits(t)
```

Reverse encoding never selects a Theta index that cannot decode back to the intended digit.

### D1 - BIP-39 Determinism

The composite function:

```text
digits -> entropy -> bits -> indices -> seed
```

is deterministic. Repeated evaluation for the same digit sequence yields identical output.

## Required Tests

- Theta reverse correctness (R1)
- Digit-space invariants
- Theta round-trip entropy fuzzer
- BIP-39 determinism (D1)

All tests must pass before claiming conformance.

## Change Control

The following fields are profile-critical:

- `theta_map`
- `digit_map`
- `digit_to_theta_indices`
- `digits_to_entropy_128`

Any modification requires a full invariant suite run and a new profile version.

## Status

Profile: v0.1
Stability: stable
Intended use: deterministic symbolic encoding to BIP-39 entropy/seed

```text
===========================================
   THETA-BIP39 ENCODING - PROFILE v0.1
              CONFORMANT
   Deterministic Theta->digit->entropy->BIP39
   Invariants: R1 (Theta correctness), D1 (determinism)
===========================================
```
