# Theta-BIP39 Encoding

## Governance Charter - Profile v0.1

### 1. Purpose

This charter defines the governance structure, responsibilities, and change-control rules for Theta-BIP39 Encoding Profile v0.1. Its purpose is to ensure that the Theta-layer symbolic encoding and BIP-39 entropy pipeline remain deterministic, auditable, and stable across implementations.

### 2. Governance Principles

1. Determinism: the encoding pipeline must behave identically across environments, platforms, and implementations.
2. Stability: core mappings and entropy rules are version-locked.
3. Transparency: all changes require explicit proposals and review.
4. Reproducibility: any output must be reproducible from the same glyph string indefinitely.
5. Minimality: no additional semantics or behaviors may be introduced outside the profile specification.

### 3. Profile Authority

The following artifacts define Profile v0.1:

- Profile manifest in JSON and TOML
- Reference TypeScript implementation
- Invariant suite for R1 and D1
- Package test runner
- CI pipeline

These documents collectively define the canonical behavior of the profile.

### 4. Required Invariants

- R1: reverse encoding may only select Theta indices whose forward expansion contains the requested digit.
- D1: the digits-to-entropy-to-bits-to-indices-to-seed pipeline is a pure function.

### 5. Change Control

Any modification to `theta_map`, `digit_map`, `digit_to_theta_indices`, or `digits_to_entropy_128` requires a new profile version, a Profile Change Proposal, and full test suite approval.

### 6. Review Process

- Minimum two reviewers
- All invariants must pass
- CI must pass
- Profile Change Proposal must document motivation, impact, and compatibility

### 7. Versioning

- v0.1 is stable
- v0.2+ must document all breaking changes
- Older profiles remain available for decoding legacy data

### 8. Enforcement

Any implementation claiming conformance to Profile v0.1 must include the conformance header, pass the full invariant suite, and use the canonical entropy and Theta-layer rules.
