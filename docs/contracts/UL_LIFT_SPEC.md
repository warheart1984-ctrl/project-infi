# UL Lift Specification

**Status:** Contract v1 (design + implementation anchor)  
**Package:** `src/usl/lift/`  
**Schema:** `schemas/ul_lifted_model.v1.json`

## Purpose

The **UL Lifter** (USL semantic lifter) decodes normalized binary substrate into a governed semantic model (`ULLiftedModel`) for AAIS registration and Forge compilation. It is **not** AAIS-UL (`src/aais_ul_substrate.py`), which handles cognitive command payloads.

## Naming

| Name | Meaning |
|------|---------|
| **USL** | Guest binary execution under capability lattice |
| **UBO** | Normalized binary object — lifter input (`meta` + raw `.text`) |
| **AAIS-UL** | Governed cognitive command substrate — orthogonal |
| **UL Lifter** | Machine-code → `ULLiftedModel` (`src/usl/lift/`) |

## Pipeline

```
Raw bytes → UBO (loaders) → ULLifter → ULLiftedModel → AAIS registry → Forge emit
```

The Exokernel courier orchestrates load and registration; see `EXOKERNEL_COURIER_SPEC.md`.

## Core type: `ULLiftedModel`

| Section | Type | Source |
|---------|------|--------|
| `meta` | `ULProgramMeta` | UBO + format headers |
| `control` | `ULControlShape` | Disassembly → CFG |
| `data` | `ULDataShape` | Segments + inferred regions |
| `effects` | `AAISEffectSurface` | Static syscall / import scan |
| `invariants` | `AAISInvariantSet` | Derived safety rules |
| `capabilities` | `AAISCapabilitySet` | Resources from effects |
| `runtime_shape` | `AAISRuntimeProfile` | Admission / health defaults |

**Provenance:** `meta.program_id` = `UBO.binary_id`; `meta.provenance.artifact_hash` matches content hash.

## Lifter orchestration

```text
lift_machine_code(ubo, text_bytes) → ULLiftedModel
  meta         ← lift_meta_from_ubo(ubo)
  control      ← lift_control_from_text(text_bytes, isa, entry)
  data         ← lift_data_from_meta(meta)
  effects      ← lift_effects_from_syscalls(control, isa, os_family)
  invariants   ← lift_invariants_from_effects(effects, meta)
  capabilities ← lift_capabilities_from_effects(effects)
  runtime_shape← lift_runtime_shape_default()
```

## ISA phased matrix

| Phase | Scope | Lifting depth |
|-------|-------|---------------|
| **P1** | ELF x86_64 Linux | meta + linear CFG + `syscall` scan → effects |
| **P2** | PE x86_64 Windows | meta via `pe.py`; effects via `syscall` / `int 0x2e` |
| **P3** | aarch64 ELF Linux | syscall convention + disasm backend switch |
| **P4** | Mach-O / WASM (optional) | import-based effects before full CFG |

**Disasm interface:** `src/usl/lift/disasm/` — backend pluggable (v1: linear x86_64 sweep).

## P1 lifting rules (v1)

### meta

- `UBO` → `ULProgramMeta`: segments as `ULSegment`, entrypoint, isa, provenance block.

### control

- Linear sweep on `.text` → basic blocks at branch targets.
- Minimal `ULFlowGraph` + function grouping at entry / symbols.

### data

- Segment kinds: `global` from `.data` / `.bss` / `.rodata`; stack/heap deferred.

### effects

- Scan for `syscall` (x86_64: `0f 05`); map register to Linux syscall table when immediate.
- Classify into `fs` / `net` / `timer` / `proc` buckets.
- Each effect carries `confidence`: `proven` | `heuristic` | `unknown`.

### invariants

- No syscalls → `no_syscall` safety invariant.
- Writable + executable segment overlap → `self_modifying` hazard.

### capabilities

- Syscall presence → `ResourceCapability` + `AuthorityLevel` mapped to `usl_capability_id`.

### runtime_shape

- Default `oneshot` / `single` until loop/blocking heuristics exist.

## Governance bridge

Binary-derived `AAISInvariantSet` compiles into `GovernanceIR.InvariantSet` via `src/invariant_compiler.py` using a lift-specific input adapter (`src/usl/lift/governance_bridge.py`).

## Limits

- Static syscall number recovery is heuristic; indirect syscalls marked `unknown`.
- Call graph incomplete when indirect calls present; Forge assumes worst-case effects unless proven.
- No JIT, self-modifying code execution, or native guest run in lifter v1.

## Related

- `EXOKERNEL_COURIER_SPEC.md` — thin mux orchestration
- `FORGE_LIFT_COMPILER_SPEC.md` — dynamic / static emission
- `USL_SPEC.md` — Layer 0 architecture
