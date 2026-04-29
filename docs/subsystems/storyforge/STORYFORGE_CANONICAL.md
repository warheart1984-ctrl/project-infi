# Story Forge Canonical

This file governs the active Story Forge subsystem inside `AAIS-main`.

It replaces the older placeholder state where Story Forge appeared only as a
concept.

If this file conflicts with runtime code, runtime code still wins.

## 1. Status

Story Forge is partially live in AAIS.

That means:

- the source packages are now vendored in-repo
- the audio/movie capability path is admitted and tested
- the full standalone Story Forge repo is no longer the default runtime source
- the entire external Story Forge product surface is not yet admitted as one
  AAIS-native front door

## 2. Core Law

Story Forge owns narrative build truth.

Applied law:

- Story Forge determines the structured narrative build
- Beatbox scores that build
- Speakers voice and mix that build
- the assembler packages the final movie artifact
- none of the downstream layers may become canonical merely by rendering

## 3. Current Admitted Runtime Boundary

The current admitted AAIS surface is:

- `src/capabilities/story_forge_audio.py`

That governed capability accepts:

- `BackendBuildArtifact`
- `rendered_video_path`
- dialogue or narration metadata

It emits:

- bounded `FinalMovieArtifact` contract data

Current source roots used by that path:

- `external/story_forge/src/story_forge`
- `external/beatbox_speakers/src`

## 4. Current Source Of Truth In Code

Primary Story Forge runtime sources:

- `external/story_forge/src/story_forge/backend_full_build.py`
- `external/story_forge/src/story_forge/movie_audio_pipeline.py`
- `external/story_forge/src/story_forge/contracts/`

Primary downstream audio sources:

- `external/beatbox_speakers/src/audio_pipeline/`
- `external/beatbox_speakers/src/beatbox/`
- `external/beatbox_speakers/src/speakers/`
- `external/beatbox_speakers/src/assembler/`

Primary AAIS integration points:

- `src/capabilities/story_forge_audio.py`
- `tests/test_story_forge_audio_capability.py`

## 5. Authority Rules

Story Forge must not bypass AAIS governance.

Current authority rules:

- live AAIS execution should enter through the governed capability path
- vendored Story Forge code is present, but that does not grant general runtime
  authority to every Story Forge module
- Beatbox and Speakers remain downstream expression layers
- downstream audio or movie output may not rewrite Story Forge narrative truth

## 6. What Is Live Today

Live or exercised today:

- backend build artifact generation
- Story Forge audio handoff contract
- Beatbox cue-plan/audio pipeline path
- Speakers voice/mix path
- final movie assembly path through the governed capability

## 7. What Is Not Yet Admitted As A First-Class AAIS Surface

Not yet admitted as broad AAIS runtime surfaces:

- the standalone Story Forge launcher
- the full movie renderer as a direct operator lane
- the text-game-to-video front door
- the game front door
- the text-to-3D world lane as an AAIS live lane
- broad direct provider use outside the governed capability boundary

## 8. Expansion Rule

Future growth should happen stage by stage.

Allowed next moves:

- harden the current admitted audio/movie chain
- expose a narrow direct Story Forge capability contract for structured source
  intake
- only after that consider broader cinematic, game, or world-pack activation

Disallowed next move:

- treating the whole vendored Story Forge tree as universally live merely
  because it is present in the repo
