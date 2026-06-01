# Story Forge Stage Spec

This file is the stage ledger for Story Forge inside `AAIS-main`.

If this file conflicts with runtime code, runtime code still wins.

## Purpose

This file answers:

- what the Story Forge stages are
- where Beatbox and Speakers enter
- which parts are admitted in AAIS today

## Core Stage Order

1. translation
2. staging
3. directional
4. presentation
5. cinematic
6. engine handoff
7. backend build
8. Beatbox scoring
9. Speakers voice and mix
10. final movie assembly

## Stage Rules

- no stage may silently own another stage's job
- Story Forge defines the narrative build before audio expression begins
- Beatbox may score the build, not rewrite it
- Speakers may voice and mix the build, not rewrite it
- assembly may package the artifact, not redefine it

## Current AAIS Admission Matrix

| Stage | Current AAIS Status | Notes |
| --- | --- | --- |
| translation | vendored, not first-class AAIS endpoint | present in vendored Story Forge contracts and lanes |
| staging | vendored, not first-class AAIS endpoint | present in vendored Story Forge contracts and lanes |
| directional | vendored, not first-class AAIS endpoint | present in vendored Story Forge contracts and lanes |
| presentation | vendored, not first-class AAIS endpoint | present in vendored Story Forge contracts and lanes |
| cinematic | vendored, not first-class AAIS endpoint | present in vendored Story Forge contracts and lanes |
| engine handoff | vendored and exercised | used by backend build tests and audio capability path |
| backend build | admitted through current capability path | produces `BackendBuildArtifact` |
| Beatbox scoring | admitted downstream inside current capability path | uses vendored Beatbox/audio pipeline |
| Speakers voice and mix | admitted downstream inside current capability path | uses vendored Speakers/audio pipeline |
| final movie assembly | admitted downstream inside current capability path | uses vendored assembler path |

## Current Entry Point

AAIS currently enters the chain after structured narrative build work is already
available.

The current admitted path begins with:

- `BackendBuildArtifact`

It does not yet begin with raw operator prose as a broad Story Forge front door.

## Next Safe Expansion

The safest next Story Forge activation is:

- a narrow direct structured-source capability

The least safe next move is:

- exposing the entire vendored Story Forge launcher surface as generally live
