# Speakers Subsystem

This folder contains the active Speakers subsystem docs for `AAIS-main`.

## What Speakers Is

Speakers is the governed voice, mix, and final audio assembly layer that sits
downstream of Beatbox.

It takes the Story Forge handoff plus Beatbox timing and score output, renders
voice stems, performs mix rules, and helps produce the final movie package.

## Active Docs In This Folder

- [SPEAKERS_CANONICAL.md](./SPEAKERS_CANONICAL.md)
  - canonical source of truth for the active Speakers surface in AAIS

## Current Runtime Status

- status: partial live
- current live role: downstream Story Forge voice/mix lane
- current live source roots:
  - `external/beatbox_speakers/src/speakers`
  - `external/beatbox_speakers/src/assembler`

## Canonical Rule

The active canonical doc in this folder is
[SPEAKERS_CANONICAL.md](./SPEAKERS_CANONICAL.md).

If Speakers docs conflict with runtime code, runtime code wins.
