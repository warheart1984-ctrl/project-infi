# AAES-OS v1.0 Replication Package

Enables independent teams to reproduce AAES-OS v1.0 results:

- CAS 1.0 behavior
- CRK-1 / UCR deterministic runtime
- CTS conformance results
- CDP-1 continuity benchmark
- CEP experiment execution

**Goal:** Validate deterministic, constitutional, reproducible behavior across independent environments.

---

## 1. Contents

```
replication/
  README.md           # This file
  run.sh              # (planned) one-shot replication script
  expected/           # (planned) golden outputs
aaes-os/
  benchmarks/cdp1/    # Minimal CDP-1 runner
  cep/                # Experiment orchestrator
  tools/              # Determinism validators
tests/crk1/           # Python CRK-1 conformance
sdk/continuity-sdk/   # CDP-1 Python harness
```

---

## 2. Requirements

- Node.js 20+
- pnpm 9+
- Python 3.11+ (CRK-1 / CDP-1 Python paths)
- Git

---

## 3. Replication Steps

### Install

```bash
git clone https://github.com/warheart1984-ctrl/Project-Infinity1.git
cd Project-Infinity1
pip install -e .
cd aaes-os && pnpm install && pnpm build
```

### Run CRK-1 / spine determinism

```bash
cd aaes-os
pnpm test:determinism
```

### Run CTS (spine)

```bash
pnpm test:cts
```

### Run CDP-1 minimal benchmark

```bash
pnpm run cdp1
```

### Python CRK-1 conformance

```bash
cd ..  # repo root
pytest tests/crk1 -q
```

### Python CDP-1 harness (optional)

```bash
python sdk/continuity-sdk/harness/cdp1_experiment.py
```

---

## 4. Expected Outputs

Golden outputs will be published under `replication/expected/` as release gates close. Your results should match published receipts and drift scores.

---

## 5. Reporting Results

Submit to the AAES-OS Governance Council:

- Receipt hashes
- CTS output
- CDP-1 drift scores
- Environment details (OS, Node, Python versions)

See [challenge protocol](../../docs/aaes-os/governance/CHALLENGES.md).

---

> **Replication is the final release gate for AAES-OS v1.0.**
