# Theta-BIP39 Encoding

## Security Audit Checklist - Profile v0.1

### Theta-Layer Integrity

- [ ] All Theta indices map to valid glyphs.
- [ ] All glyphs used in Theta forward decoding map to valid digits.
- [ ] No Theta index produces an empty digit set.
- [ ] No Theta index produces digits outside 0-13.

### Reverse Mapping (R1)

- [ ] For each digit `d`, every Theta index `t` in `reverse(d)` satisfies `d in forward_digits(t)`.
- [ ] No Theta index is assigned to a digit it cannot produce forward.
- [ ] Reverse mapping is deterministic.

### Digit-Space Invariants

- [ ] Every digit 0-13 has at least one Theta index.
- [ ] No digit is unreachable.
- [ ] No Theta index is unused unless explicitly deprecated.

### Entropy Function

- [ ] Entropy is `SHA256(digits_to_bytes(digits))[:16]`.
- [ ] No alternative hashing or truncation rules.
- [ ] No environment-dependent behavior.

### BIP-39 Determinism (D1)

- [ ] Entropy to bits to indices to seed is deterministic.
- [ ] Checksum bits follow BIP-39.
- [ ] Word indices are stable across runs.
- [ ] Seed derivation uses PBKDF2-HMAC-SHA512 with 2048 rounds.

### Round-Trip Properties

- [ ] `digits -> Theta -> glyphs -> digits'` preserves entropy.
- [ ] Fuzzer with 200+ cases shows no entropy drift.
- [ ] No Theta-layer collisions produce divergent seeds.

### Implementation Hygiene

- [ ] No probabilistic decoding in canonical path.
- [ ] No fallback heuristics in canonical path.
- [ ] No external dependency affects determinism.

### Change Control

- [ ] No modifications to profile-critical fields without version bump.
- [ ] Profile Change Proposal exists for any proposed change.
- [ ] Reviewers have approved the change.
- [ ] CI pipeline passes all tests.

### Documentation

- [ ] Conformance header present.
- [ ] Manifest updated.
- [ ] README updated.
- [ ] Test vectors updated.
