# AAIS Capability Module Spec

Version: 1.0  
Type: subsystem_spec  
Scope: universal_capability_adapter

## Purpose

The AAIS Capability Module is a governed adapter that translates AAIS intent
into external capability execution and returns deterministic AAIS-native
results.

It exists to ensure:

- no provider failure leaks into runtime
- all outputs are normalized
- all failures are structured and auditable

## Core Law

A capability module must do one job only:

Translate governed AAIS intent into execution and return a deterministic
AAIS-native result.

## System Position

`AAIS -> Capability Module -> External Provider`

The module is the only allowed boundary between AAIS and:

- APIs
- local tools
- file systems
- external engines

## Governing Rules

1. One job, one purpose.
2. No raw exceptions cross the boundary.
3. All outputs must be normalized.
4. All failures must be deterministic.
5. Provider logic is isolated inside the module.
6. Semantic validation is required before admission.
7. Governance visibility is mandatory.

## Result Contract

### Success Object

```json
{
  "ok": true,
  "module": "<module_name>",
  "action": "<action_name>",
  "data": {},
  "meta": {}
}
```

### Failure Object

```json
{
  "ok": false,
  "module": "<module_name>",
  "action": "<action_name>",
  "error_type": "<ErrorType>",
  "message": "<human_readable>",
  "details": {}
}
```

## Error Taxonomy

- `InputError`
- `NetworkError`
- `FileError`
- `PermissionError`
- `TimeoutError`
- `APIError`
- `ProviderUnavailable`
- `EncodingError`
- `SemanticError`
- `SchemaError`
- `UnsupportedFormat`
- `ExecutionError`
- `UnknownError`

## Protection Model

### Boundary Guard

The boundary guard contains network failures, file errors, API errors, and
timeouts so external instability never leaks into AAIS.

### Semantic Guard

The semantic guard rejects malformed results, missing fields, empty content,
and schema violations before admission into AAIS.

### Deterministic Error Object

Every failure path must end in a structured AAIS-native error object. No raw
exception, raw provider payload, or silent failure may cross inward.

## Execution Flow

1. Receive intent.
2. Validate input.
3. Translate to provider format.
4. Execute under boundary guard.
5. Perform semantic validation.
6. Normalize result.
7. Return AAIS object.

## Module Types

### Image Module

Actions:

- `analyze`
- `generate`
- `edit`

### Music Module

Actions:

- `analyze_track`
- `detect_bpm`
- `classify_mood`
- `generate_loop`
- `transform_style`

### Document Module

Actions:

- `summarize`
- `extract_fields`
- `classify`
- `rewrite`
- `convert_format`

## Governance Requirements

Each execution should expose:

- `module`
- `action`
- `provider`
- `timestamp`
- `trace_id`
- `result_size`
- `error_type` when failure occurs

## Testing Requirements

### Success Tests

- valid input -> valid normalized output

### Boundary Tests

- timeout
- missing file
- network failure

### Semantic Tests

- malformed response
- missing fields
- invalid schema

## Extension Rules

A module may only be admitted if:

- bounded purpose is defined
- input contract is explicit
- deterministic result contract is implemented
- boundary guard exists
- semantic guard exists
- error taxonomy is respected
- tests exist

## Doctrine Summary

A capability module is a sealed translator:

- AAIS law outside
- provider complexity inside
- deterministic truth returned at the boundary
