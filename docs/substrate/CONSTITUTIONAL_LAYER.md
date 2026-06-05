# Constitutional Layer (Meta Architect Lawbook)

Normative spec for the AAIS constitutional spine — maps human constitution to machine enforcement.

## Authority

| Layer | Path | Role |
|-------|------|------|
| Human constitution | `lawbook/META_ARCHITECT_LAWBOOK.md` | Supreme governance text |
| Machine constitution | `src/substrate/meta_law_engine.py` | Load, digest, invariant emission |
| Runtime attachment | `src/project_infi_law.py` | `constitutional_context` on `require_contract()` |

Tracked copies under `lawbook/` are substrate artifacts. Root-local originals (`META_ARCHITECT_LAWBOOK.md`) may remain gitignored.

## Precedence

Constitutional precedence aligns with AAIS Spine (`src/aais_composed_runtime.py`):

**Law > Blueprint > Contract > Implementation > Pipeline > Tool**

Meta Lawbook governs `project_infi_law` (law_1..law_9); it does not replace it. When both apply, constitutional context is attached and `law_0_supreme_precedence` is evaluated when the lawbook is present.

## Tier

Same substrate tier as:

- naming genome
- SSP bundles
- UL substrate
- governance bootstrap (`tests/governance_bootstrap.py`)
- invariant engine

## Invariants (machine-emitted, not free text)

`meta_law_engine` emits structured invariant checks:

| Invariant ID | Source doctrine | Enforcement |
|--------------|-----------------|-------------|
| `constitutional_precedence` | Constitutional Precedence | Spine order present |
| `proof_of_reality` | Doctrine I | Claim taxonomy required |
| `trust_bundle` | Doctrine XI | Trust bundle schema reference |
| `fail_closed` | Mandatory No-Bypass / Doctrine IV | Fail-closed posture armed |
| `ma_12_operational_primer` | Doctrine XII | README operational primer |
| `ma_13_copilot_integrator` | Doctrine XIII | Stage 2 doctrine reference |

## Bootstrap

- Lawbook fail to load → refuse start when `AAIS_REQUIRE_CONSTITUTIONAL_LAW=1`
- Dev: graceful degrade to `status: absent` when lawbook missing and flag unset
- Wired in `tests/governance_bootstrap.py` via `ensure_constitutional_substrate()`

## Gate

```bash
python3 tools/governance/check_meta_law.py
```

Makefile target: `meta-law-gate`

## Related

- [INGRESS_COLLABORATION_MEMBRANE.md](./INGRESS_COLLABORATION_MEMBRANE.md) — charter ingress (subordinate)
- [../runtime/AAIS_SUBSYSTEM_SPEC.md](../runtime/AAIS_SUBSYSTEM_SPEC.md) — subsystem map
- [../../document/law/REPO_LAWBOOK.md](../../document/law/REPO_LAWBOOK.md) — repo law front door
