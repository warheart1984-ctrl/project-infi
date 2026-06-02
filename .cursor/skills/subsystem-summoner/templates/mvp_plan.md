# {{TITLE}} — MVP Plan

CISIV stage: concept → implementation target

Status: {{STATUS}}

Concept origin: [./{{CONCEPT_SPEC_FILE}}](./{{CONCEPT_SPEC_FILE}})

## 1. Minimal Runtime Surface

| Surface | Planned location | Notes |
|---------|------------------|-------|
| {{SURFACE_1}} | {{LOCATION_1}} | {{NOTES_1}} |

## 2. Code Artifacts

{{CODE_ARTIFACTS}}

## 3. Tests

{{TESTS}}

## 4. Fixtures

{{FIXTURES}}

## 5. Gates

| Gate | Script | Sequence |
|------|--------|----------|
| {{GATE_NAME}} | {{GATE_SCRIPT}} | {{GATE_SEQUENCE}} |

## 6. Proof Bundle

Target: `docs/proof/{{PROOF_SUBDIR}}/{{PROOF_PACKET}}.md`

| Claim | Label | Evidence |
|-------|-------|----------|
| {{PROOF_CLAIM_1}} | `none_yet` | Requires implementation |
| {{PROOF_CLAIM_2}} | `none_yet` | Requires verification |

## 7. Reproduction Commands

```bash
{{REPRODUCTION_COMMANDS}}
```

## 8. Activation Dependencies

**Existing subsystems required:** {{EXISTING_DEPS}}

**Order among batch:** {{BATCH_ORDER}}

**Rationale:** {{ORDER_RATIONALE}}
