# Wolf CoG OS Seam (Stage 3)

## Build-Time

`wolf-cog-os/forge/governance/substrate-invariants.json` defines `runtime_scorpion_invariants` with evaluator cross-refs.

## Post-Build Ingest (inactive)

```bash
# Default: no-op
wolf-cog-os/scripts/scorpion-ingest-boot-trace.sh /path/to/boot_trace.ndjson

# Activation
export SCORPION_WOLF_INGEST=active
wolf-cog-os/scripts/scorpion-ingest-boot-trace.sh /path/to/boot_trace.ndjson
```

Claim: `asserted` until boot trace captured on hardware/VM and proof bundle filed.
