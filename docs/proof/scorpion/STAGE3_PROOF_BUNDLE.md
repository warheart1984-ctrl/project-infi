# Scorpion Stage 3 Proof Bundle

Claim: **asserted** (Wolf seam documented; live ingest inactive).

## Evidence

- `wolf-cog-os/forge/governance/substrate-invariants.json` — `runtime_scorpion_invariants`
- `docs/subsystems/scorpion/WOLF_COG_SEAM.md`
- `wolf-cog-os/scripts/scorpion-ingest-boot-trace.sh` exits 0 when inactive

## Activation Criteria for `proven`

Boot trace from CoGOS image on VM + ingest with `SCORPION_WOLF_INGEST=active` + scan drift report archived here.
