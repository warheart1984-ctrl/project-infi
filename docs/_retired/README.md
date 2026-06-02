# Retired Subsystems

This folder holds documentation for subsystem families that have completed the
[retirement protocol](../contracts/AAIS_SUBSYSTEM_RETIREMENT_PROTOCOL.md).

Nothing here is live system truth.

## Layout

```text
docs/_retired/<gene>/
  README.md           # retirement summary + successor link
  RETIREMENT_PROOF.md # optional copy or link to docs/proof/
```

## Rules

- Genome `identity.stage` MUST be `deprecated` or `retired`
- Genome `ssp.summon_eligible` MUST be `false`
- Runtime code removal only after retirement proof and two stable releases with shim

## Current Retirements

| Gene | Retired | Successor |
|------|---------|-----------|
| *(none)* | — | — |
