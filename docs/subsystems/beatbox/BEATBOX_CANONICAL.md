# Beatbox Canonical

This file governs the active Beatbox subsystem surface inside `AAIS-main`.

If this file conflicts with runtime code, runtime code still wins.

## Status

Beatbox is partially live in AAIS as a downstream Story Forge audio lane.

## Core Law

Beatbox never owns narrative truth.

Beatbox sits between Story Forge and Speakers.

That means:

- Story Forge provides structured narrative and timing truth
- Beatbox turns that truth into score cues and audio artifacts
- Speakers receive Beatbox output and continue the audio chain

## Current Runtime Sources

- `external/beatbox_speakers/src/beatbox/`
- `external/beatbox_speakers/src/audio_pipeline/`
- `external/ai/beatbox/adapter.py`
- `integrations/contracts/beatbox_contract.md`

## Current AAIS Role

Beatbox is currently admitted as part of the Story Forge audio capability path.

It is not yet a separate broad operator-facing AAIS lane.

## Input And Output Shape

Current core shapes:

- `ScoreRequest`
- `BeatboxCuePlan`
- `BeatboxArtifact`
- `BeatboxResult`

## Rule Of Expansion

If Beatbox grows beyond the current Story Forge audio chain, it should still
stay behind a governed contract and should not gain narrative-truth ownership.
