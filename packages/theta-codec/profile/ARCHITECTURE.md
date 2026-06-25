# Theta-BIP39 Encoding

## Profile v0.1 Architecture

```text
Glyph String (G*)
  |
  | decode
  v
Theta Indices (Theta*)
  |
  | forward delta(g)
  v
Digits (D*)
  |
  | base-14 integer
  v
Raw Bytes (big-endian)
  |
  | SHA-256
  v
128-bit Entropy (E)
  |
  | BIP-39 checksum
  v
132-bit BIP-39 Bitstring
  |
  | split into 11-bit words
  v
12 BIP-39 Word Indices
  |
  | PBKDF2-HMAC-SHA512
  v
BIP-39 Seed
```

This diagram is canonical for Profile v0.1.
