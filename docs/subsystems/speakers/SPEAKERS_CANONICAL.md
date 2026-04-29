# Speakers Canonical

This file governs the active Speakers subsystem surface inside `AAIS-main`.

If this file conflicts with runtime code, runtime code still wins.

## Status

Speakers is partially live in AAIS as a downstream Story Forge audio lane.

## Core Law

Speakers renders and mixes expression.
It does not own narrative truth and it does not own score truth.

Applied law:

- Story Forge provides narrative build truth
- Beatbox provides score and timing truth
- Speakers renders voice, applies mix rules, and prepares final audio/movie
  output

## Current Runtime Sources

- `external/beatbox_speakers/src/speakers/`
- `external/beatbox_speakers/src/assembler/`
- `external/beatbox_speakers/src/audio_pipeline/`

## Current AAIS Role

Speakers is currently admitted through the Story Forge audio capability path.

It is not yet a separate broad operator-facing AAIS subsystem lane.

## Input And Output Shape

Current core shapes:

- `SpeakersVoicePlan`
- `SpeakersMixPlan`
- voice stem manifest
- final mixed audio path
- assembled movie output path

## Rule Of Expansion

If Speakers grows into a wider AAIS surface, it must stay downstream of Story
Forge and Beatbox contracts and must not become a truth-owning layer.
