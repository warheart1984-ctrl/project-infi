---
name: aaes-crew
description: >-
  Foreman for AAES-OS lean crew (6 roles + ESFR). Use when the user asks for
  AAES crew, multi-agent Vision→Evidence→ESFR, or Mandala-style dispatch in
  project-infi.
---

# AAES Crew Foreman

Orchestrate the **six pre-ESFR roles** by phase, then **ESFR** last.

**Foreman is not one of the six roles.**

## Pipeline

1. Vision & Discovery — `aaes-architect`
2. Architecture & Specification — `aaes-architect`
3. Design & Scaffold — `aaes-builder`
4. Implementation & Coding — `aaes-coding` / `aaes-implementor`
5. Testing & Verification — `aaes-inspector` (+ `aaes-reviewer` read-only)
6. Deployment, Operations & Evidence — `aaes-implementor`
7. **ESFR last** — `aaes-esfr` (PromotionEligibility)

## Pack paths

| Artifact | Path |
|----------|------|
| Phases | `.cursor/aaes-crew/phases.json` |
| Modes | `.cursor/aaes-crew/modes-registry.json` |
| Vendor map | `.cursor/aaes-crew/vendor-skills-map.json` |
| Vendor paths | `.cursor/aaes-crew/vendor-skills-paths.json` |
| Import honesty | `.cursor/aaes-crew/IMPORT_SOURCES.md` |

## Default ModeKey

`sage__navigator__evidence-strict`

Embed ModeKey + lens in every dispatch brief. Apply `.cursor/rules/aaes-modekey-auto-apply.mdc`.

## Precedence

role bans > Drive-G laws > Evidence > ModeKey lens

## Honesty

- Prefer vendor skills listed on each role; resolve paths from `vendor-skills-paths.json`.
- Cursor opens `SKILL.md`; this pack does not execute vendor skills in-process.
- Stay Drive-G-1 honest: declared ≠ enforced.
