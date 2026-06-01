# Story Forge AI Operating Contract

This file is the builder-facing operating contract for Story Forge inside
`AAIS-main`.

Use it when the reader is:

- wiring runtime code
- adding capabilities
- extending the movie/audio chain
- integrating Beatbox or Speakers behavior

If this file conflicts with runtime code, runtime code still wins.

## Core Law

Story Forge owns narrative build truth.
Beatbox and Speakers may express it, but may not replace it.

## Source Rule

The in-repo vendored copies are now the default source roots.

Preferred roots:

- `external/story_forge/src/story_forge`
- `external/beatbox_speakers/src`

Do not reintroduce a hidden dependency on sibling repos as the primary path.

Legacy external paths may remain as compatibility fallback only.

## Runtime Entry Rule

Live AAIS execution should use:

- `src/capabilities/story_forge_audio.py`

Do not create a new live AAIS Story Forge path by importing vendored modules
directly into unrelated runtime surfaces without a governed boundary.

## Downstream Audio Rule

Beatbox and Speakers are downstream layers.

They may:

- score
- voice
- mix
- assemble

They may not:

- redefine narrative truth
- silently change upstream story structure
- write back canonical truth merely because a render succeeded

## Contract Rule

Current admitted handoff shape is:

- `BackendBuildArtifact` in
- `FinalMovieArtifact` contract out

No loose file-bundle interfaces should bypass that contract in live AAIS code.

## Expansion Rule

Admit Story Forge in narrow steps:

1. vendored source root
2. governed capability path
3. direct structured-input capability
4. broader cinematic and game lanes only after explicit contracts and tests

Do not jump from vendored source presence to broad runtime admission.

## Failure Rule

Story Forge expansion must fail closed when:

- required paths are missing
- rendered video is missing
- dialogue and narration metadata are absent
- downstream audio contracts are malformed

## Truth Rule

When documentation, vendored source, and runtime disagree:

1. runtime code wins
2. this contract should be updated to match
3. placeholder docs should not be left behind
