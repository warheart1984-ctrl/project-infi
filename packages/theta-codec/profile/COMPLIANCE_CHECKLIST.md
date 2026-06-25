# Theta-BIP39 Encoding Profile v0.1 Compliance Checklist

- [ ] Theta-layer forward mapping is total.
- [ ] Reverse mapping satisfies R1.
- [ ] Digit-space invariants hold for digits 0..13.
- [ ] Entropy function is canonical: `SHA256(digits_to_bytes(digits))[:16]`.
- [ ] BIP-39 pipeline is deterministic.
- [ ] Full invariant suite passes.
- [ ] No probabilistic decoding is used in the canonical BIP-39 path.
- [ ] Change control is followed for sensitive mapping or entropy changes.
