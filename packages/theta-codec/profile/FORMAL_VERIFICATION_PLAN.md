# Theta-BIP39 Encoding

## Formal Verification Plan - Profile v0.1

### Objective

Formally verify that the Theta-to-digit-to-entropy-to-BIP-39 pipeline satisfies invariants R1 and D1 and that the implementation is free of structural, semantic, and determinism defects.

## 1. Formal Model

### Domains

- Theta indices: `Theta = {0..T}`
- Digits: `D = {0..13}`
- Glyphs: finite set `G`
- Entropy: `E = {0,1}^128`
- BIP-39 indices: `I = {0..2047}`

### Functions

- `g : Theta -> G`
- `delta : G -> D*`
- `R : D -> P(Theta)`
- `f1 : D* -> E`
- `f2 : E -> {0,1}^132`
- `f3 : {0,1}^132 -> I^12`
- `f4 : I^12 -> S`

Composite pipeline:

```text
B = f4 . f3 . f2 . f1 . decode
```

## 2. Properties To Verify

### R1 - Theta-Reverse Correctness

For all `d in D` and `t in R(d)`:

```text
d in delta(g(t))
```

### D1 - BIP-39 Determinism

For all `X in D*`:

```text
B(X) = B(X)
```

and for any environments `E1`, `E2`:

```text
B(X, E1) = B(X, E2)
```

### Round-Trip Entropy Preservation

For all `X in D*`:

```text
f1(X) = f1(decode(encode(X)))
```

### No Structural Collisions

For all `X`, `Y in D*`:

```text
encode(X) = encode(Y) => f1(X) = f1(Y)
```

## 3. Verification Methods

- Exhaustive symbolic checking over all Theta indices.
- Property-based fuzzing over digit sequences.
- Hash-stability testing across supported environments.
- Static analysis for randomness, time dependence, and external state.
- Manual review of mapping and entropy drift.

## 4. Acceptance Criteria

The profile is verified when all invariants hold, fuzz tests pass, determinism tests pass, no structural collisions are found, CI is green, and reviewers approve.

## 5. Deliverables

- Verification report
- Updated manifest
- Updated test vectors
- CI logs
- Reviewer sign-off
