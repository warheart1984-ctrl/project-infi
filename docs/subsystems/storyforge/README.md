# Story Forge Subsystem

This folder contains the active Story Forge subsystem docs for `AAIS-main`.

## What Story Forge Is

Story Forge is the governed narrative-to-cinematic build stack inside AAIS.

It takes structured story material, turns it into validated narrative build
artifacts, and hands those artifacts to downstream audio and movie layers.

Story Forge owns narrative build truth.
Beatbox and Speakers may express that truth, but they do not replace it.

## Active Docs In This Folder

- [STORYFORGE_CANONICAL.md](./STORYFORGE_CANONICAL.md)
  - canonical active source of truth for Story Forge inside AAIS
- [STORYFORGE_HUMAN_GUIDE.md](./STORYFORGE_HUMAN_GUIDE.md)
  - human-first explanation of what Story Forge does and how it behaves
- [STORYFORGE_AI_OPERATING_CONTRACT.md](./STORYFORGE_AI_OPERATING_CONTRACT.md)
  - builder-facing rules for integrating or extending Story Forge
- [STORYFORGE_STAGE_SPEC.md](./STORYFORGE_STAGE_SPEC.md)
  - stage map for Story Forge plus Beatbox and Speakers handoffs

## Current Runtime Status

- status: partial live
- admitted AAIS surface: `src/capabilities/story_forge_audio.py`
- vendored runtime sources:
  - `external/story_forge/src/story_forge`
  - `external/beatbox_speakers/src`
- current downstream audio chain:
  - Story Forge backend build
  - Beatbox scoring
  - Speakers voice and mix
  - assembler final movie package

## Canonical Rule

The active canonical doc in this folder is
[STORYFORGE_CANONICAL.md](./STORYFORGE_CANONICAL.md).

If Story Forge docs conflict with runtime code, runtime code wins.
