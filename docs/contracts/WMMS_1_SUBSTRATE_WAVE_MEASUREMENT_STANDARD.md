# WMMS-1 Substrate to Wave Measurement Standard

Continuity Standards Track - Measurement Specification

Author: Jon Halstead
Category: Continuity Science
Status: Draft Standard
Implementation: `src/continuity/wave_math.py`

## 0. Abstract

WMMS-1 defines how a continuity-native node derives operational wave
parameters from observable substrate data.

Every wave parameter must be computable from substrate fields. No wave value is
an opinion or manually supplied conclusion.

## 1. Measurement Output

```text
WaveSignature {
  A: Float
  f: Float
  phi: Float
  C: Float
  R: Float
}
```

The implementation uses `WaveSignature.to_dict()` and emits:

- `A`: amplitude
- `f`: frequency
- `phi`: phase
- `C`: coherence
- `R`: resonance

## 2. CSSENS-1 Sensor Inputs

The sensor extraction function is `substrate_observables()`.

It consumes:

- `ContinuitySubstrate.ccs_layer.events`
- `ContinuitySubstrate.trace_layer.traces`
- `CCSStore.events`
- `CCSStore.traces`
- event context fields
- trace continuity summary fields
- trace reproducibility metadata

## 3. Required Observables

WMMS-1 measurement requires:

- `identity_count`
- `system_count`
- `lineage_depth`
- `governance_impact`
- `architectural_scope_score`
- `pattern_count`
- `time_window`
- `declared_intent_vector`
- `observed_behavior_vector`
- `lineage_direction_vector`
- `replay_divergence`
- `cross_kernel_disagreement`
- `cross_layer_mismatch`
- `lineage_pointer_mismatch`
- `invariant_violation_rate`
- `pattern_persistence`
- `natural_frequency`
- `governance_reinforcement_cycles`

Missing required observables fail closed.

## 4. Measurement Functions

### Amplitude A

Impact strength across identity, systems, lineage, governance, and architecture:

```text
A = mean(
  normalize(identity_count),
  normalize(system_count),
  normalize(lineage_depth),
  governance_impact,
  architectural_scope_score
)
```

### Frequency f

Pattern recurrence over the measurement window:

```text
f = pattern_count / time_window
```

### Phase phi

Alignment between declared intent, observed behavior, and lineage direction:

```text
phi = mean(
  cosine(declared_intent_vector, observed_behavior_vector),
  cosine(observed_behavior_vector, lineage_direction_vector)
)
```

### Coherence C

Cross-layer stability:

```text
C = 1 - mean(
  replay_divergence,
  cross_kernel_disagreement,
  cross_layer_mismatch,
  lineage_pointer_mismatch,
  invariant_violation_rate
)
```

### Resonance R

Long-term stability and lock-in:

```text
R = max(
  pattern_persistence * (1 - abs(f - natural_frequency)),
  A * normalize(governance_reinforcement_cycles)
)
```

## 5. Operational Bridge

This standard completes the substrate to wave bridge:

```text
ContinuitySubstrate -> CSSENS-1 observables -> WMMS-1 measurement -> WaveSignature
```

The bridge makes continuity drift, governance instability, resonance collapse,
phase drift, coherence decay, and fracture risk measurable in real time.

## 6. Verification

Runtime tests:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_wave_math_measurement_standard.py -q
```

The current proof covers:

- derivation of `A`, `f`, `phi`, `C`, and `R` from real CCS substrate fields
- preservation of source references
- fail-closed behavior for missing observables
