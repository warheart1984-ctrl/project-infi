# Subsystem Genome Registry

SSP Alt-4 DNA records for AAIS subsystem families.

Meta-schema: [schemas/subsystem_genome.v1.json](../../schemas/subsystem_genome.v1.json)

Contract: [docs/contracts/AAIS_SUBSYSTEM_GENOME.md](../../docs/contracts/AAIS_SUBSYSTEM_GENOME.md)

## Gate

```bash
make genome-gate
make alt4-gate
make alt5-gate
```

## Registered Genomes

| Gene | Stage | File |
|------|-------|------|
| `cisiv_operator_lineage_console` | governed | [cisiv_operator_lineage_console.genome.v1.json](./cisiv_operator_lineage_console.genome.v1.json) |
| `forensic_triangulation` | governed | [forensic_triangulation.genome.v1.json](./forensic_triangulation.genome.v1.json) |
| `narrative_trust_pack` | governed | [narrative_trust_pack.genome.v1.json](./narrative_trust_pack.genome.v1.json) |
| `recipe_module` | governed | [recipe_module.genome.v1.json](./recipe_module.genome.v1.json) |
| `imagine_generator` | governed | [imagine_generator.genome.v1.json](./imagine_generator.genome.v1.json) |
| `human_voice_extraction` | governed | [human_voice_extraction.genome.v1.json](./human_voice_extraction.genome.v1.json) |
| `safety_envelope_organ` | mvp | [safety_envelope_organ.genome.v1.json](./safety_envelope_organ.genome.v1.json) |
| `operator_profile_organ` | mvp | [operator_profile_organ.genome.v1.json](./operator_profile_organ.genome.v1.json) |

## Adding a Genome

On SSP summon (Step 7), create `<gene>.genome.v1.json` at `stage: concept` with
empty `runtime.surface` and `proof.posture: asserted`.

Update this table and run `make genome-gate`.
