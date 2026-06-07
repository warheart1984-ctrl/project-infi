# Story Forge Text-to-3D Game Lane Design

Date: 2026-06-07

## Goal

Build Story Forge's third lane as a governed text-to-3D video game creation pipeline. The lane must accept a text prompt, produce a structured game/world specification, and generate a deterministic playable 3D browser prototype from that specification.

The first implementation should make `text_to_3d_world_lane_organ` a real execution-producing lane instead of a `not_configured` stub, while preserving the existing governance posture and capability bridge routing.

## Existing Context

The repo already contains the Story Forge expansion fabric:

- `src/text_to_3d_world_lane_organ.py`
- `src/game_front_door_organ.py`
- `src/text_game_to_video_organ.py`
- `src/capabilities/story_forge_organs.py`
- `external/story_forge/src/story_forge/text_to_3d_world_lane.py`
- `external/story_forge/src/story_forge/engine.py`
- `external/story_forge/src/story_forge/worldpacks/`

The current `text_to_3d_world_lane` bridge route returns `route_status: not_configured` unless forced. Release docs describe this as a known stub. The new work should turn that lane into a deterministic generation path without bypassing operator gating.

## Pipeline

The lane will implement this flow:

```text
text prompt
-> prompt intake
-> deterministic game intent parse
-> GameWorldSpec build
-> gameplay rules compile
-> 3D scene manifest build
-> playable browser prototype export
-> WorldPack manifest
-> proof and bridge response
```

The pipeline must be deterministic. The same prompt plus the same seed must produce the same `GameWorldSpec`, manifest, and playable artifact metadata.

## Core Artifacts

### GameWorldSpec

`GameWorldSpec` is the canonical structured output. It should be JSON-serializable and engine-neutral.

It includes:

- `schema_version`
- `world_id`
- `seed`
- `title`
- `genre`
- `camera`
- `player`
- `controls`
- `objectives`
- `win_conditions`
- `loss_conditions`
- `zones`
- `spawn_points`
- `entities`
- `interactions`
- `hazards`
- `lighting`
- `asset_placeholders`
- `engine_targets`

### Gameplay Spec

The gameplay spec compiles player-facing behavior from the world spec:

- movement model
- camera behavior
- collect/use/interact rules
- objective tracking
- collision and hazard behavior
- deterministic scoring
- completion state

### Scene Manifest

The scene manifest maps the world spec into renderable scene data:

- geometry primitives
- materials
- lights
- spawn transforms
- entity transforms
- collision bounds
- UI labels
- deterministic asset placeholder IDs

### Playable3DPrototype

The first renderer should be a static browser-playable 3D prototype. It can use a deterministic Three.js runtime or an equivalent existing local browser runtime if one is already present.

The prototype must be playable enough to validate the lane:

- player movement
- camera
- objective display
- interactable objects
- win condition
- reset/replay
- deterministic scene layout

### WorldPack

The lane writes a portable world pack containing:

- `world.spec.json`
- `gameplay.spec.json`
- `scene.manifest.json`
- `playable_manifest.json`
- `index.html` or equivalent playable entry
- `lane_receipt.json`

Later engines can consume the JSON files without depending on the browser prototype.

## Execution Route

`execute_text_to_3d_world_lane_route()` should accept:

- `prompt`
- `seed` optional
- `session_id` optional
- `operator_ack` or equivalent gate
- `export_playable` default true

The route should return:

- `ok`
- `organ`
- `action`
- `lane_id`
- `route_status`
- `aais_live_lane`
- `proposal_only`
- `world_id`
- `world_spec_ref`
- `world_pack_ref`
- `playable_ref`
- `receipt`
- `message`

Operator gating remains required for artifact-producing execution. When the prompt or gate is missing, the route returns a structured block response instead of generating artifacts.

## Game Front Door

`game_front_door_organ` should admit a `/pipeline game` session into this lane. It should preserve the existing session admission checks, then route prompt-based game creation to `text_to_3d_world_lane` when requested.

The front door should not duplicate world-building logic. It should call the lane route and report the lane receipt.

## Data Flow

Prompt intake normalizes user text and seed. The deterministic parser extracts genre, mood, spatial hints, objective verbs, nouns, hazards, and win conditions. The world spec builder turns those signals into a bounded scene graph with stable IDs. The gameplay compiler creates rules from that graph. The playable exporter renders the result into a static artifact. The route returns references and a receipt.

No external model call is required for the first implementation. The lane should use deterministic local parsing so tests are stable and the output is replayable. Model-assisted enrichment can be added later behind the same spec contract.

## Error Handling

The route blocks when:

- prompt is empty
- operator gate is missing for artifact generation
- artifact output directory is unavailable
- generated spec fails validation
- playable export fails

Block responses must include `ok: false`, `claim_label: blocked`, and a short `message`.

Generation responses must include `claim_label: asserted` and enough artifact references for verification.

## Storage

Generated world packs should live under a bounded Story Forge runtime/export directory. A suitable initial target is:

```text
.runtime/story_forge/text_to_3d_world/<world_id>/
```

The implementation must avoid writing outside the repo root and must not mutate governance files during runtime execution.

## API And Bridge

The existing capability bridge registration for `text_to_3d_world_lane` should remain the execution entry point. The status API should reflect whether the lane module and execution proof are present, and whether the lane is live.

The status response should move from:

```text
route_status: not_configured
aais_live_lane: false
```

to:

```text
route_status: configured
aais_live_lane: true
```

when the executable lane and proof are present.

## Testing

Unit tests should cover:

- deterministic prompt parsing
- stable world ID/spec output for prompt plus seed
- world spec validation
- gameplay spec generation
- scene manifest generation
- playable artifact export
- blocked response for empty prompt
- blocked response for missing operator gate
- successful `execute_text_to_3d_world_lane_route()`
- `game_front_door_organ` routing into the lane
- status reporting the live lane when proof/module preconditions are met

Verification should include the existing Story Forge organ tests plus new focused tests for the pipeline.

## Non-Goals For First Slice

- Photorealistic assets
- AI image, mesh, video, or voice generation
- Unity, Unreal, or Godot export
- Networked multiplayer
- Persistent user accounts
- Runtime mutation of governance genomes

These can be layered later because the structured world/game specs are engine-neutral.

## Acceptance Criteria

The work is complete when:

- A prompt plus seed creates a valid `GameWorldSpec`.
- The same prompt plus seed produces stable output.
- The lane writes a portable world pack.
- The playable export opens as a browser 3D prototype.
- The capability bridge route returns artifact references.
- The game front door can admit and route a game creation request.
- Tests prove blocked and successful paths.
- The existing Story Forge status and gate tests still pass.
