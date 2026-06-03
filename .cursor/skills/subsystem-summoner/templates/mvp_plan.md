# {{TITLE}} — MVP Plan

CISIV stage: concept → implementation target

Status: {{STATUS}}

Concept origin: [./{{CONCEPT_SPEC_FILE}}](./{{CONCEPT_SPEC_FILE}})

## 1. Minimal Runtime Surface

| Surface | Planned location | Notes |
|---------|------------------|-------|
| {{SURFACE_1}} | {{LOCATION_1}} | {{NOTES_1}} |

## 2. Code Artifacts

**Naming protocol checklist**

- [ ] Mythic + Engineering names recorded in concept spec §1
- [ ] Module stem is snake_case engineering name (not `*_organ.py` / `*_fabric.py`)
- [ ] Primary class is `<Domain><Function><Role>` PascalCase
- [ ] File header + dual-layer comments per [AAIS_CODEX_CURSOR_NAMING_PROTOCOL.md](../../../docs/contracts/AAIS_CODEX_CURSOR_NAMING_PROTOCOL.md)
- [ ] Public functions are verb-led; no mythic identifiers in symbols
- [ ] Genome `ssp.engineering_class` set (documentation field until schema gene ships)

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
