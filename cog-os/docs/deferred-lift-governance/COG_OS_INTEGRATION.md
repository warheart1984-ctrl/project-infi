# cog-os integration map

How **Deferred Lift / Governance** artifacts land on the CoG OS guest and which forge hooks own them.

## Guest layout (target)

```
/opt/cogos/usl-lifted/          # Lifted static forge output + registry-facing artifacts
/opt/cogos/lib/fixtures/usl/    # Optional baked ELF fixtures (minimal.elf)
```

Runtime policy also looks for decode material relative to forge bundle roots; staging into `usl-lifted` keeps guest admission self-contained.

## Forge profile

**`cog-os/forge/profiles/usl-lifted-guest.yaml`**

- `payload_usl_lifted: true` — enables USL lifted payload staging in forge build.
- Services: `platform`, `usl`
- Gates: `usl_health_200`, `usl_broker_ready`, plus standard init/platform gates.

## Payload scripts

| Script | Role |
|--------|------|
| `cog-os/forge/scripts/lib/payload-stage-usl.sh` | USL runtime (lift/forge/exo Python tree, broker, start scripts) |
| `cog-os/forge/scripts/lib/payload-stage-usl-lifted.sh` | Ensures `/opt/cogos/usl-lifted`; optionally runs `ExokernelCourier.lift_and_register_from_path` on `tests/fixtures/usl/minimal.elf` during rootfs build |

Invocation pattern:

```bash
COG_REPO_ROOT=/path/to/project-infi \
  bash cog-os/forge/scripts/lib/payload-stage-usl-lifted.sh "$ROOTFS_DIR"
```

## Environment (guest / forge host)

| Variable | Purpose |
|----------|---------|
| `USL_GOVERNANCE_ADMISSION` | `compiler` (decode bundle) or `severity` (fallback map) |
| `USL_DISASM_BACKEND` | `linear` (default) or `capstone` |
| `USL_AAIS_REGISTRY_DIR` | Persistent JSON registry directory for lifted models |
| `USL_LIFT_ELF` | Path to ELF for dynamic lift-at-boot via broker (`bootstrap_forge_runtime`) |
| `USL_FORGE_DIR` | Directory containing `gate_policy.json` and lifted forge artifacts |

### Profile defaults (`USL_GOVERNANCE_ADMISSION`)

Staged in `/etc/cog/policies/default-capability-bundle.json` and applied by `start-usl` when the bundle is present:

| Profile | Default admission | Notes |
|---------|-------------------|--------|
| `usl-lifted-guest` | `compiler` | Requires `/opt/cogos/usl-lifted/governance_decode_bundle.json` from forge bake |
| `daily-driver` | `compiler` when governance bundle exists; else `severity` | Broker + operator UI on Cinnamon |
| `metal` | `severity` | No lifted bake unless `payload_usl_lifted: true` |

Guest `start-usl` sets `USL_LIFT_ELF=/opt/cogos/lib/fixtures/usl/minimal.elf` when that file exists so broker lift works without re-running forge on an installed system.

## Governance bundle (guest)

After `payload-stage-usl-lifted.sh` runs `ExokernelCourier.lift_and_register_from_path`, the guest image must contain:

```
/opt/cogos/usl-lifted/governance_decode_bundle.json
/opt/cogos/usl-lifted/gate_policy.json
/opt/cogos/usl-lifted/lifted_model.json
```

The staging script fails the build if `governance_decode_bundle.json` is missing after a successful lift bake.

## Operator refresh (installed system)

Refresh lifted artifacts on a deployed guest **without** re-running the full forge rootfs build:

1. Copy updated ELF + forge outputs to `/opt/cogos/usl-lifted/` (or lift a new ELF into that directory).
2. Ensure `governance_decode_bundle.json` and `gate_policy.json` accompany the lifted model.
3. Set or confirm env (often via `/etc/cog/services/usl` or service wrapper):
   - `USL_LIFT_ELF=/path/to/artifact.elf`
   - `USL_FORGE_DIR=/opt/cogos/usl-lifted`
   - `USL_GOVERNANCE_ADMISSION=compiler` when the decode bundle is present
4. Restart USL: `systemctl restart cog-usl` or `/opt/cogos/bin/start-usl` per profile init mode.
5. Verify: `curl -sf http://127.0.0.1:8766/health` and broker registry under `USL_AAIS_REGISTRY_DIR`.

Optional: use `ExokernelCourier.lift_and_register_from_path` on the forge host, then rsync `/opt/cogos/usl-lifted/` to the guest.

## Logging (guest)

Service scripts append to `/var/log/cog/{platform,aais,usl,desktop}.log`. Forge gate `cog_logs_present` checks script wiring on built rootfs.

## Package channel (`cog-pkg` v1)

`/opt/cogos/bin/cog-pkg` wraps `apt-get` with profile scoping and provenance:

```bash
cog-pkg channel-show          # profile + /etc/cog/policies/default-capability-bundle.json
sudo cog-pkg install -y pkg   # delegates to apt-get; logs to registry dir
cog-pkg provenance-tail 20
```

Requires `/etc/cog/profile` (staged by `payload-stage-policies.sh`).

## Proof alignment

- Boot/service proof: see [../BOOT_PROOF_CHECKLIST.md](../BOOT_PROOF_CHECKLIST.md) (`usl` service, health gate).
- USL slice admit scripts: `cog-os/scripts/test/usl-slice1-admit.sh`, `usl-slice2-admit.sh`.
- WSL dev (native staging, pip deps): [../../../docs/operations/USL_WSL_DEV.md](../../../docs/operations/USL_WSL_DEV.md).
- This folder tracks **lift/governance-specific** gaps; use [REMAINING_WORK.md](./REMAINING_WORK.md) for backlog.

## Operator continuity recovery mode

Hardware migration re-binds **operator identity** (sovereign Ed25519 root → `operator_id = H(pubkey)`) to new CoGOS hardware. Device hostname/Linux user from installer identity are **viewport only**, not operator root identity.

### CoGOSDATA layout

```
/var/lib/cogos/operator_substrate/{operator_id_slug}/
  ledger.jsonl          # append-only signed events
  root_identity.json    # pubkey + operator_id (public)
  recovery_state.json   # last import tier, pending_re_attestation
  operator-root-key.json  # secret key (restrictive permissions)
```

Override runtime root with `AAIS_RUNTIME_DIR` (same as AAIS/UGR acceleration paths).

### Recovery boot

| Mechanism | Purpose |
|-----------|---------|
| `COGOS_RECOVERY=1` | Kernel cmdline or firstboot env — skip normal operator UI until import |
| `cogos-operator-recovery import --file PATH` | Local verify + apply before AAIS/USL start |
| Recovery UI | Minimal paste/upload in `operator_ui_server.py` recovery route |

### Transport

USB JSON → API paste → mesh pull → QR stub (v1 doc only).

Contracts: `docs/contracts/OPERATOR_CONTINUITY_INVARIANT.md`, `docs/contracts/OPERATOR_RECOVERY_PACKET.md`.
