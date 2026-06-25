# Runtime Initialization Contract

Status: **active**

Mythic label (docs only): *Genesis Protocol*

Engineering contract: `RuntimeInitializationAdmission`

## Purpose

Define **bounded boot and initialize** behavior for AAIS/CoG OS. Initialization is an admission decision with explicit inputs, outputs, and failure codes—not ambient startup folklore.

## Inputs

| Input | Description |
|-------|-------------|
| `data_dir` | Governed data root (e.g. `data/`) |
| `config_snapshot` | Launcher/config resolved state |
| `lawbook_ref` | Path or hash of `META_ARCHITECT_LAWBOOK.md` |
| `genome_registry_snapshot` | Optional subsystem genomes under `governance/subsystem_genomes/` |

## Outputs

```python
# Conceptual shape — align with launcher/state machine as implemented
class InitializationAdmissionResult:
    allowed: bool
    reason_code: str  # e.g. OK, MISSING_SCHEMA, LAWBOOK_DRIFT, GATE_FAILED
    checks: list[str]   # human-readable check names run
```

## Preconditions (must pass before `allowed=True`)

1. **MA-12 operational primer** — README and ops sections satisfy operational law ([Doctrine XII](../../META_ARCHITECT_LAWBOOK.md)).
2. **Dependency gate** — lockfiles and policy per [DEPENDENCY_GATE_POLICY.md](../contracts/DEPENDENCY_GATE_POLICY.md).
3. **Canonical doc lane** — no accidental authority from archive trees ([AAIS_DOC_PROTOCOL.md](../contracts/AAIS_DOC_PROTOCOL.md)).
4. **Governance Makefile targets** — documentation baseline and agent-safety validators runnable locally.

## Entry points

| Surface | Path |
|---------|------|
| AAIS launcher | `aais/launcher.py` (`doctor`, start flows) |
| State machine | `src/project_infi_state_machine.py` |
| CLI | `python -m aais start` (see `aais/` package) |

## Failure modes

| `reason_code` | Meaning | Operator action |
|---------------|---------|-----------------|
| `MISSING_SCHEMA` | Required DB/schema artifact absent | Run migrations or `doctor` |
| `LAWBOOK_DRIFT` | Lawbook hash mismatch vs expected | Review release notes; do not assert complete |
| `GATE_FAILED` | Doc or agent-safety gate failed | Fix governance drift before runtime admit |
| `CONFIG_INVALID` | Launcher config incomplete | Fix `operator_kernel.config.yaml` / env |

## Non-goals

- This contract does **not** replace OTEM stage receipts for individual tool runs.
- This contract does **not** grant agents authority to mutate constitutional files on boot.

## Related law

- [src/project_infi_law.py](../../src/project_infi_law.py) — runtime law substrate
- [CUOS_FOUNDATION_LAWS.md](../contracts/CUOS_FOUNDATION_LAWS.md) — foundation admission rules
