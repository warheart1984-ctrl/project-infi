# Story Forge Human Guide

This file explains Story Forge in plain language.

Use it when you want to know:

- what Story Forge is
- why it is different
- how it behaves
- what is live now

If this file conflicts with runtime code, runtime code still wins.

## What Story Forge Is

Story Forge is the part of AAIS that turns structured story material into a
movie-ready build.

It is not just a text generator.
It is a governed build chain with contracts between stages.

## Why Story Forge Is Different

Story Forge keeps one important rule:

- the story build decides what is true

Everything after that is expression:

- Beatbox turns the build into score cues
- Speakers turn the build into voiced lines and mix plans
- the assembler turns the video and audio into a final movie package

The render is not allowed to become the canon.

## What Is Live Right Now

The currently live AAIS path is narrower than the full Story Forge product.

Right now AAIS can:

- accept a Story Forge backend build artifact
- run the downstream audio/movie pipeline through a governed capability
- return a bounded final movie artifact contract

Right now AAIS does not yet expose the whole Story Forge launcher or every
Story Forge lane as a first-class operator surface.

## How It Behaves

Story Forge is fail-closed and stage-bound.

That means:

- later stages do not get to rewrite earlier truth
- missing required inputs block the run
- downstream audio is an expression layer, not a new source of truth
- the capability returns a bounded contract instead of a loose bundle of files

## How Beatbox And Speakers Fit

Beatbox and Speakers are part of the Story Forge output chain, but they are not
the same subsystem responsibility.

The practical split is:

- Story Forge: narrative build and handoff truth
- Beatbox: score generation and music cue timing
- Speakers: voice rendering, ducking, mixing, and final audio packaging

## What To Read Next

1. `STORYFORGE_CANONICAL.md`
2. `STORYFORGE_AI_OPERATING_CONTRACT.md`
3. `STORYFORGE_STAGE_SPEC.md`
4. `../beatbox/BEATBOX_CANONICAL.md`
5. `../speakers/SPEAKERS_CANONICAL.md`
