# CSS-1 Continuity Specimen Standard

Continuity Standards Track - Scientific Specimen Format

Status: Implemented
Implementation: `src/continuity/specimens.py`
Reference library: `specimens/`

## 1. Purpose

CSS-1 defines the canonical format for observed continuity. A continuity
specimen is the continuity equivalent of a biological genome file: it preserves
events, lineage, measured metrics, wave signature, proof receipt, and
experimental conditions.

## 2. Schema

```text
ContinuitySpecimen {
  specimen_id: String
  specimen_type: baseline | identity_reinforcement | governance_conflict | continuity_fracture
  thread_id: String
  events[]
  lineage[]
  metrics
  wave
  receipt
  conditions
}
```

Events must declare:

- `event_id`
- `event_type`
- `timestamp`
- `kernel`: `UGR`, `AAIS`, `DARZ`, or `AAES`
- `payload`

Lineage relations must be one of:

- `CAUSES`
- `DERIVES_FROM`
- `CONSTRAINS`
- `VIOLATES`
- `REINFORCES`

## 3. CSL-1 Library Structure

```text
specimens/
  001_baseline/
    specimen.json
    lineage_graph.json
    wave_signature.json
    receipt.json
    replay_trace.json
```

The same required files exist for specimens 002-004.

## 4. Canonical Specimens

| ID | Type | Purpose |
|----|------|---------|
| `css1.001.baseline` | baseline | healthy control signature |
| `css1.002.identity_reinforcement` | identity_reinforcement | identity resonance and lineage strengthening |
| `css1.003.governance_conflict` | governance_conflict | governance-identity misalignment |
| `css1.004.continuity_fracture` | continuity_fracture | collapse conditions and replay fracture |

## 5. SGP-1 Specimen Generation

DAR-Z can produce CSS-1 specimens from runtime state using:

```text
Event Stream
  -> Lineage Builder
    -> Metrics Engine (CSSENS-1)
      -> Wave Engine (WMMS-1)
        -> Receipt Engine
          -> Specimen Exporter
```

Implementation:

- `generate_specimen_from_runtime()`
- `export_specimen_artifacts()`

## 6. SRVP-1 Replay and Validation

`validate_specimen()` checks:

- CSS-1 schema shape
- kernel and lineage relation enums
- lineage pointers
- wave range validity
- proof status
- replay stability

Fracture specimens are allowed to be schema-valid while replay/proof validation
fails. Collapse is data, not malformed data.

## 7. SCE-1 Comparison

`compare_specimens()` computes:

```text
delta_A
delta_f
delta_phi
delta_C
delta_R
lineage_distance
classification
```

This supports continuity clustering, morphology analysis, anomaly detection,
and drift forecasting.

## 8. SMC-1 Morphology Classes

`morphology_class()` classifies specimens as:

- `harmonic_continuity`
- `identity_dominant_continuity`
- `governance_dominant_continuity`
- `chaotic_continuity`
- `fractured_continuity`

## 9. SLC-1 DAR-Z Specimen Lifecycle

`DarzSpecimenArchive` provides first-class node memory for specimens:

- specimen export
- specimen ingestion
- specimen archival
- specimen listing for comparison/federation workflows

Specimen federation is carried by FCP-1 as continuity artifacts.

## 10. Verification

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_continuity_specimens.py -q
```
