# Theta-BIP39 Encoding

## Threat-Mitigation Matrix - Profile v0.1

| Threat Class | Description | Mitigation |
| --- | --- | --- |
| Theta-layer ambiguity | Multi-digit glyphs can create ambiguity. | R1 ensures reverse encoding only selects indices producing the requested digit. |
| Non-deterministic decoding | Probabilistic or heuristic decoding can diverge. | Canonical path forbids probabilistic decoding through D1. |
| Mapping drift | Silent changes to maps can change seeds. | Version locking, change control, and manifest governance. |
| Entropy collisions | Different digits can theoretically produce same entropy. | SHA-256 preimage resistance and fuzz testing for structural collisions. |
| Seed divergence | Same glyph string can produce different seeds if implementation drifts. | Deterministic pipeline and CI enforcement. |
| Implementation bugs | Incorrect expansion or Theta selection. | Full invariant suite plus round-trip fuzzer. |
| Environment drift | Different platforms produce different outputs. | Pure functions and deterministic runtime APIs. |
| Unreachable digits | Some digits cannot be encoded. | Digit-space invariant tests. |
| Unused Theta indices | Theta indices unused or incorrectly mapped. | Theta-layer invariant tests and review. |
| Unauthorized profile changes | Breaking changes without version bump. | Profile Change Proposal process and governance charter. |
