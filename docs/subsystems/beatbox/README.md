# Beatbox Subsystem

This folder contains the active Beatbox subsystem docs for `AAIS-main`.

## What Beatbox Is

Beatbox is the governed audio scoring lane that sits downstream of Story Forge
and upstream of Speakers.

It turns structured shot and emotional data into score cues and audio artifacts.

## Active Docs In This Folder

- [BEATBOX_CANONICAL.md](./BEATBOX_CANONICAL.md)
  - canonical source of truth for the active Beatbox surface in AAIS

## Current Runtime Status

- status: partial live
- current live role: downstream Story Forge scoring lane
- current live source roots:
  - `external/beatbox_speakers/src/beatbox`
  - `external/beatbox_speakers/src/audio_pipeline`

## Canonical Rule

The active canonical doc in this folder is
[BEATBOX_CANONICAL.md](./BEATBOX_CANONICAL.md).

If Beatbox docs conflict with runtime code, runtime code wins.
