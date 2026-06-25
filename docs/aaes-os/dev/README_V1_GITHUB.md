# AAES-OS v1.0

## A Constitutional Architecture for Governed Intelligence

AAES-OS is an open, deterministic operating system for governed AI systems. It enforces constitutional constraints, produces verifiable receipts, and enables reproducible continuity experiments.

## What's Included

- CAS 1.0 Specification
- CAS Reference Implementation
- CRK-1 Deterministic Runtime
- CTS Conformance Test Suite
- Continuity Experimental Platform (CEP)
- CDP-1 Benchmark
- Independent Replication Package
- Governance Handbook
- Developer Guide

## Quick Start

### Install

```bash
git clone https://github.com/warheart1984-ctrl/Project-Infinity1.git
cd Project-Infinity1
pip install -e .
cd aaes-os && pnpm install && pnpm build
```

### Run CRK-1 conformance tests

```bash
pytest tests/crk1 -q
```

### Run CDP-1 harness

```bash
python sdk/continuity-sdk/harness/cdp1_experiment.py
```

### Run AAES-OS spine tests

```bash
cd aaes-os && pnpm test
```

## Documentation

| Topic | Link |
|-------|------|
| CAS / Constitution | [docs/aaes-os/governance/CONSTITUTION.md](../governance/CONSTITUTION.md) |
| CRK-1 | [src/crk1/](../../../src/crk1/) |
| CDP-1 spec | [docs/crk1/continuity/CDP1_CONSTITUTIONAL_SPEC.md](../../crk1/continuity/CDP1_CONSTITUTIONAL_SPEC.md) |
| Governance | [docs/aaes-os/governance/](../governance/) |
| Tutorials | [docs/aaes-os/dev/TUTORIALS.md](TUTORIALS.md) |

## Reproducibility

v1.0 includes:

- Deterministic runtime
- Reproduction scripts
- Drift metrics
- Continuity graphs
- Challenge-response protocol

## Contribute

Pull requests, issues, and independent replications are welcome. AAES-OS is designed to be challenged.

See [CONTRIBUTING.md](../../../aaes-os/CONTRIBUTING.md).

## License

Apache 2.0 (Project-Infinity1). See repository `LICENSE`.
