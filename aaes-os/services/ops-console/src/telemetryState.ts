import {
  DriftMetrics,
  FaultJournal,
  PatchAnalytics,
  PatternLedger,
} from '@aaes-os/aaes-governance';

import { seedTelemetry } from './seedTelemetry.js';

export const faultJournal = new FaultJournal();
export const patternLedger = new PatternLedger();
export const patchAnalytics = new PatchAnalytics();
export const driftMetrics = new DriftMetrics();

let seeded = false;

/** Ensures demo telemetry exists for local development. */
export function ensureTelemetrySeeded(): void {
  if (seeded) {
    return;
  }
  seedTelemetry(faultJournal, patternLedger, patchAnalytics);
  seeded = true;
}
