# Nova Touch Input Design

This file documents the Nova touch-input design boundary for `AAIS-main`.

Its job is to explain the intended touch surface without pretending that touch
is already installed in the live runtime.

If this file conflicts with runtime code, runtime code still wins.

## Core Truth

The current live Nova interaction surface is keystroke-driven input.

That means:

- typed input is the active operator interaction path
- keyboard rhythm may appear in supporting runtime signals
- touch semantics are not active runtime truth yet

This file is explanatory design, not proof of live touch behavior.

## Why This File Exists

Nova interaction design should be documented clearly before new touch behavior
is implemented.

Without that boundary, docs can drift into implying:

- touch is already live when it is not
- touch changes identity or authority
- touch silently alters continuity or immune behavior

This file prevents that drift.

## Current Installed Input Surface

Right now Nova should be described as:

- keystroke-first
- text-led
- companion-surface driven
- still subordinate to Jarvis authority

Not as:

- gesture-native
- touch-governed
- haptic-reactive
- sensor-driven

Those may become future surfaces, but they are not live today.

## Design Rule

Touch design may explain possible future interaction shapes, but it must not
change current law:

- Jarvis remains the authority lane
- Nova remains the companion lane
- input modality does not grant new authority
- touch does not bypass memory, continuity, watchdog, or operator override law

## Future Touch Scope

If touch is added later, it should be treated as a bounded interaction layer,
not as a personality or authority rewrite.

Possible future touch classes may include:

- tap as bounded selection or acknowledgement
- hold as deliberate emphasis or confirmation
- swipe as surface navigation
- multi-step gesture as explicit mode request

These are design categories only.

They are not installed behavior in the current workspace.

## Current Non-Goals

This doc does not activate:

- haptics
- gesture recognition
- biometric sensing
- affect detection from touch
- immune coupling from touch signals

Those remain out of scope until explicitly implemented and tested.

## Keystroke Rule

Because keystroke is the only active input path right now:

- all live Nova behavior should still be explained from typed interaction first
- touch language must not replace keystroke truth in docs
- builders should leave other future touch parts alone until they are explicitly
  scoped

## Read With

Read this file alongside:

1. `NOVA_HUMAN_GUIDE.md`
2. `NOVA_AI_OPERATING_CONTRACT.md`
3. `NOVA_STAGE_SPEC.md`
4. `SUPER_NOVA_CANONICAL.md`
