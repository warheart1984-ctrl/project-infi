---
title: Sovereign IDE
description: The shared seven-surface cockpit for the live Nova desktop shell and the docs site parity view.
---

import { SovereignIdeSurfaceMap } from '../../src/components/SovereignIdeSurfaceMap';

# Sovereign IDE

The Sovereign IDE is the shared operator-facing composition of the live Nova desktop shell and the docs-site
visualizer pages. It presents the same seven surfaces, the same API hook vocabulary, and the same governed runtime
story in both places so the guide and the implementation stay aligned. When the live runtime is running, this page
hydrates from `http://127.0.0.1:8787` by default, or from the `SOVEREIGN_IDE_API_BASE_URL` environment variable if
you set one.

Run `npm start` in `docs-site` to build the docs, launch the Sovereign IDE API server on `127.0.0.1:8787`, and
serve the visualizer against that live surface in one step. The command also opens the browser directly to the
visualizer page after both servers are ready.

Use `npm start -- --browser=headless` if you want the same startup flow without opening a browser, or
`npm start -- --browser-path=/docs/visualizer/sovereign-ide` to target a different docs route.

<SovereignIdeSurfaceMap />

## Live surface map

| Surface | Purpose | Backend | Frontend | API hook |
|---|---|---|---|---|
| Temporal Replay Timeline | Replay governed epochs and audit continuity | Sovereign Ledger Explorer v2 | `TimelineCanvas`, `EventNodes`, `ContinuitySyncIndicator` | `GET /api/timeline?epoch=<int>` |
| Quantum Glyph Shader Engine | Modulate visual resonance and glow | Harmonic Engine constants | `DynamicPulse`, `RotationalHarmony`, GLSL shader layer | `POST /api/shader/update` |
| Federated AI Organism Monitor | Track node vitality and telemetry | Telemetry Analyzer + AAES-OS node metrics | `MetricsPanel`, Chart.js graphs, organism map | `GET /api/organism/state` |
| Governance Consensus Map | Show quorum and vote flow | Promotion v2.0 Protocol | Radial consensus graph and filter panel | `GET /api/consensus/votes` |
| Sovereign Ledger Explorer v2 | Inspect proof blocks and lineage signatures | Proof Block Generator + Ledger Controller | 3D blockchain viewer and proof overlays | `GET /api/ledger/blocks` |
| Neural Mandala Composer | Convert pulse data into audio-visual composition | Harmonic Engine pulse data | WebAudio + shader-driven mandala | `POST /api/audio/pulse` |
| ULX Workbench | Compile selected source, run bytecode, and trace evidence | ULX core + governance bridge | ULX source editor, action buttons, selection mirror, shared source snapshot, and evidence receipt | `POST /api/ulx/compile` |

## Shared runtime controls

The live shell exposes the same control points through the top bar and the Sovereign IDE panel:

- `Focus timeline`
- `Focus shader`
- `Focus monitor`
- `Focus consensus`
- `Focus ledger`
- `Focus mandala`
- `Focus ULX`
- `Sync runtime` refreshes the live node status and evidence snapshots
- The ULX workbench publishes a shared source snapshot and evidence receipt so the docs cockpit and desktop bridge mirror the same highlighted fragment with a replayable proof trail

## Canonical contract

The docs page mirrors the live shell contract:

- one governing node status line
- one seven-surface visual map
- one API hook list
- one build roadmap
- one environment requirement list
- one launcher command pair (`sovereign-ide` and `python -m sovereign_ide --bootstrap-only`)

That keeps the shell and the docs site anchored to the same operator model instead of drifting into separate vocabularies.

## Build roadmap

1. Constitutional bootstrapping and invariant freeze
2. Infrastructure bedrock and governed execution kernel
3. Platform services for runtime telemetry and evidence
4. Application core for the seven sovereign surfaces
5. Integration fabric, federation, and replay proof
6. Intelligence and automation under governed routing

## Environment

- Python 3.10+
- Node.js 18+
- WebGL 2 capable browser or renderer
- Sovereign Ledger and Federation Synchronizer modules
- AAES-OS node connected for telemetry and evidence pulls

## Related pages

- [Nova Shell](../runtime/nova-shell.md)
- [Governance Dashboard](./governance-dashboard.md)
- [Runtime Core](../runtime/runtime-core.md)
- [Overview](../overview.md)
