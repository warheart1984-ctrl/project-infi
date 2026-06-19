# Nova LSG Bootstrap Contract v1

This contract defines how lawful Nova loads Long-Scale Graph (LSG) facts for
CLI and API runtimes, and how those facts connect to UGR continuity invariants.

Machine-readable bundle: [`../../lsg/LSG-CORE.v1.yaml`](../../lsg/LSG-CORE.v1.yaml)

Fixture mappings:

- [`../../fixtures/lsg/UL-LSG-MAP.v1.yaml`](../../fixtures/lsg/UL-LSG-MAP.v1.yaml)
- [`../../fixtures/lsg/Theta-LSG-REG.v1.yaml`](../../fixtures/lsg/Theta-LSG-REG.v1.yaml)
- [`../../fixtures/lsg/UGR-LSG-BIND.v1.yaml`](../../fixtures/lsg/UGR-LSG-BIND.v1.yaml)

Executable harness:
[`../../tests/test_lawful_nova_lsg.py`](../../tests/test_lawful_nova_lsg.py)

## Environment variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `NOVA_LSG_PATH` | `<repo>/lsg/LSG-CORE.v1.yaml` | YAML bundle to compile into triples |
| `NOVA_LSG_STORE` | `~/.nova/lsg/local.jsonl` | Tenant-scoped JSONL graph store |
| `LAWFUL_NOVA_REPO_ROOT` | current working directory | Repo root for default bundle resolution |
| `NOVA_UGR_STRICT` | unset | When `1`, fail closed on UGR invariant violations |

## Bootstrap commands

From repo root (`project-infi`):

```bash
# Linux / macOS
./scripts/nova-bootstrap-lsg.sh

# Windows PowerShell
.\scripts\nova-bootstrap-lsg.ps1
```

The loader is idempotent: it skips seeding when the bundle marker
`lsg-bundle:LSG-CORE@1.0` is already present in the JSONL store.

## Runtime factory

`nova.runtime_factory.build_lawful_llm()` is the single entry point used by:

- `python -m nova chat`
- `nova-api` `/v1/chat`
- `nova health` diagnostics

It calls `ensure_lsg_store()` before constructing `LawfulLLM`, so conversational
prompts match LSG triples instead of returning the empty-store fallback.

## Expected conversational behavior

After bootstrap:

```bash
python -m nova chat "hello"
python -m nova chat "how are you"
```

Expected:

- Response text cites LSG facts (not `no matching LSG facts`)
- `receipt_verified: True`
- `decision: EXECUTED`
- Receipt payload includes `continuity_invariants` with seven `pass` entries

Nonsense prompts may still fall back to the empty-match message while remaining
`EXECUTED` under RSL.

## UGR continuity invariants

Runtime checks live in `nova/governance/ugr_invariants.py` and are attached to
signed receipts as `continuity_invariants`. Declarative definitions are mirrored
in `fixtures/lsg/UGR-LSG-BIND.v1.yaml` for documentation parity.

When `NOVA_UGR_STRICT=1`, any failed invariant raises `GovernanceViolationError`
before the turn is signed.

## Shell integration

PowerShell `nova-chat` forwards arguments:

```powershell
nova-chat "how are you"
```

Lawful Nova shell bootstrap (`lawful-nova-shell/setup/bootstrap.ps1`) optionally
runs `scripts/nova-bootstrap-lsg.ps1` after environment setup.
