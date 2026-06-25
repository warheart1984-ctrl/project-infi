# Tutorial 8 — Independent Replication

## Replication package

v1.0 includes:

- CRK-1 deterministic runtime
- CTS conformance tests
- CDP-1 benchmark harness
- Reproduction scripts
- Challenge-response protocol

## Steps for external teams

1. Clone [Project-Infinity1](https://github.com/warheart1984-ctrl/Project-Infinity1)
2. `pip install -e .` and `cd aaes-os && pnpm install && pnpm build`
3. Run `pytest tests/crk1` and `pnpm test` in `aaes-os/`
4. Execute CDP-1 harness
5. Publish results (Zenodo, paper, or GitHub Discussion)

## Challenge

If results differ from published claims, file a [kernel challenge](../governance/CHALLENGES.md).

## Zenodo

Reference release: https://doi.org/10.5281/zenodo.20587377
