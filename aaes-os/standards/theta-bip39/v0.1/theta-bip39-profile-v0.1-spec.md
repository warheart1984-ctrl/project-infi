# Theta-BIP39 Encoding Profile v0.1

## RFC-Style Specification

Status: Stable  
Profile: `Theta-BIP39-Encoding`  
Version: `0.1`  
Category: Standards Track  
Intended Audience: Implementers, auditors, cryptographic engineers  
Canonical package: `@aaes-os/theta-codec`

## 1. Purpose

Theta-BIP39 Encoding Profile v0.1 defines a deterministic, version-locked
conversion from Theta-layer glyph strings into base-14 digit sequences, 128-bit
entropy, BIP-39 checksum bits, 11-bit word indices, mnemonic words, and seed
material.

This document is the normative reference for conformant implementations. The
profile exists so independent implementations can reproduce the same
symbolic-to-entropy behavior without relying on probabilistic decoding,
environment state, alternative hashing, or implementation-specific choices.

## 2. Definitions

- **Glyph:** A symbolic token in the Theta language.
- **Theta index:** A numeric choreography index whose `theta_map` entry resolves
  to a glyph.
- **Digit:** A base-14 digit in the inclusive range `0..13`.
- **Forward expansion:** The deterministic digit sequence produced by a glyph.
- **Reverse choreography:** The deterministic selection of Theta indices for a
  digit sequence.
- **Canonical path:** The default profile path. It forbids fuzzy correction,
  randomness, time dependence, and probabilistic branching.
- **Conformance Header:** A declaration in implementation docs or source stating
  that the implementation targets Theta-BIP39 Encoding Profile v0.1 and is
  bound by R1 and D1.

## 3. Normative Pipeline

```text
glyphs -> Theta indices -> digits -> entropy_128 -> bip39_bits -> indices -> mnemonic -> seed
```

The reverse path is:

```text
digits -> Theta choreography -> glyphs
```

The entropy function is:

```text
SHA256(digits_to_bytes(digits))[:16]
```

`digits_to_bytes` interprets the digit sequence as a base-14 integer and emits
the minimal big-endian byte representation. Leading zero digits therefore do not
change the entropy projection.

## 4. Invariants

### R1 - Theta-Reverse Correctness

For every digit `d` and every Theta index `t` selected during reverse encoding:

```text
d in forward_digits(theta_map[t])
```

No reverse encoder may select a Theta index for a digit that the index cannot
produce in the forward path.

### D1 - BIP-39 Determinism

For any digit sequence `X`, this function is pure and deterministic:

```text
digits -> entropy_128 -> bip39_bits -> indices -> seed
```

No random source, clock, environment variable, network call, heuristic repair,
or probabilistic branch is permitted in the canonical path.

## 5. Canonical Mappings

The canonical mappings are version-locked in `reference_implementation.ts`.
Profile-critical tables include:

- `digitMap`
- `digitLookup`
- `thetaMap`
- derived `digit_to_theta_indices`
- `digitsToEntropy128`

Any change to these tables or functions requires a new profile version.

## 6. Reverse Encoding

Reverse encoding derives `digit_to_theta_indices` from the forward mappings.
For each digit, the encoder cycles deterministically through the Theta indices
that can produce that digit.

Compound glyphs are allowed in non-strict choreography only when R1 holds. A
compound glyph may expand to more digits than the single digit that selected it,
so compound paths are not one-digit round trips. Strict single-digit choreography
filters compound glyphs and may report compound-only digits as unavailable.

## 7. BIP-39 Projection

For 128-bit entropy:

- checksum length is 4 bits
- combined entropy plus checksum length is 132 bits
- 132 bits are split into twelve 11-bit indices
- each index addresses a 2048-word BIP-39 wordlist
- seed derivation uses PBKDF2-HMAC-SHA512 with 2048 rounds and salt
  `mnemonic` plus passphrase

## 8. Test Requirements

Conforming implementations must pass:

- R1 reverse correctness over all derived reverse paths
- digit-space coverage over digits `0..13`
- strict choreography entropy round-trip fuzzing
- BIP-39 deterministic projection tests
- test vector verification from `test_vectors.json`
- reproducibility lock verification from `reproducibility_lock.json`

## 9. Security Considerations

This profile defines deterministic encoding behavior. It is not by itself a
wallet, custody system, key-management layer, or randomness source.

Implementations must not:

- treat symbolic glyph input as secret entropy without operational review
- add fuzzy correction to the canonical path
- silently change mappings
- use alternative hashing, checksum, or seed-derivation rules
- accept partial test-vector conformance as full conformance
- derive production wallet material without a real BIP-39 wordlist and explicit
  key-management controls

## 10. Versioning

Profile v0.1 is stable. Any profile-critical change requires:

1. A Profile Change Proposal.
2. A new profile version.
3. Updated test vectors.
4. Updated reproducibility lock.
5. Full invariant verification.

## 11. Conformance Claim

An implementation may claim Theta-BIP39 Profile v0.1 conformance only if it
passes the full invariant suite, test vectors, and reproducibility harness for
this directory, and includes the Profile v0.1 Conformance Header.
