# Deferred Lift / Governance Roadmap (cog-os)

Living documentation for the **Deferred Lift / Governance** implementation in `project-infi`, with emphasis on what ships in **cog-os** rootfs staging and what remains.

## Documents

| File | Purpose |
|------|---------|
| [IMPLEMENTATION_STATUS.md](./IMPLEMENTATION_STATUS.md) | What was delivered in Python/USL/Forge (by phase) |
| [REMAINING_WORK.md](./REMAINING_WORK.md) | Per-phase and global gaps still open |
| [COG_OS_INTEGRATION.md](./COG_OS_INTEGRATION.md) | Forge profiles, payload scripts, guest paths (`/opt/cogos/usl-lifted`) |

## Related repo paths

- **Lift + governance (Python):** `src/usl/lift/governance_bridge.py`, `src/invariant_compiler.py`, `src/usl/forge/`
- **cog-os staging:** `cog-os/forge/scripts/lib/payload-stage-usl-lifted.sh`, `payload-stage-usl.sh`
- **Guest profile:** `cog-os/forge/profiles/usl-lifted-guest.yaml`
- **Contracts:** `docs/contracts/FORGE_LIFT_COMPILER_SPEC.md`, `docs/contracts/EXOKERNEL_COURIER_SPEC.md`

## Verification (developer)

From repo root with venv active:

```powershell
cd e:\project-infi
.\.venv\Scripts\python.exe -m pytest tests/test_usl_governance_bridge.py tests/test_usl_lift_pe.py tests/test_usl_lift_aarch64.py tests/test_usl_disasm_backend.py tests/test_usl_registry_persist.py tests/test_usl_exo_courier.py -q
```

Rebuild USL fixtures when disasm/PE bytes change:

```powershell
.\.venv\Scripts\python.exe tests\fixtures\usl\build_fixtures.py
```
