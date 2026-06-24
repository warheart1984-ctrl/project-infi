# continuity-engine

A runtime library for observer-centric continuity systems.

## Overview

`continuity-engine` implements the full observer-centric continuity architecture:

- **CSS-2 v1.0** — Threshold stewardship + threshold emergence
- **CRK-1** — Constitutional invariants + observer protection
- **JPSS-2** — Observer development pipeline
- **RA-COS-1** — Evidence loop + trace subsystem
- **Transformation Law** — Reality → Truth → Memory → Continuity → Evolution

The library provides threshold governance, observer lifecycle governance, drift and capture detection, evidence production, recalibration governance, constitutional enforcement, lineage tools, and a CLI.

This is the first runtime designed not to preserve systems, but to preserve **reality-responsive observers**.

## Core principle

**Reality is the source. Evidence is the test. Architecture is the consequence.**

Continuity is defined as:

> The preserved capacity of a system to produce, sustain, and protect observers who can detect, interpret, and correct divergences between the system and reality.

## Installation

```bash
npm install ./continuity-engine
```

Or from the monorepo:

```bash
cd continuity-engine && npm install && npm run build
```

## Quick start

```typescript
import {
  runEvidenceLoop,
  InMemoryObserverTraceStore,
  InMemoryThresholdRegistry,
  evaluateObserverStewardship,
} from "continuity-engine";
```

## Scripts

| Command | Description |
|---------|-------------|
| `npm run build` | Compile TypeScript to `dist/` |
| `npm test` | Run test suite |
| `npm run demo` | Run evidence loop demo |
| `npm run lint` | Typecheck (`tsc --noEmit`) |

## Key lifecycles

**Observer:** Person → Observer → Senior Observer → Steward

**Threshold:** ObservationPattern → ProtoThreshold → Threshold → Δ-Threshold

**System:** Calibration → Recalibration → Constitutional Recalibration

## Documentation

See [docs/API.md](./docs/API.md) for the full API reference.

## License

MIT — see [LICENSE](./LICENSE).
