import type { SovereignXHardwareDecision } from '@aaes-os/sovereignx-router';

import type { SovereignXHardwareSnapshot } from './SovereignXHardwareTelemetryAdapter.js';

export type SovereignXHardwareOverrideDrillRequest = {
  requestedDecision?: SovereignXHardwareDecision;
  authority?: string;
  reason?: string;
};

export type SovereignXHardwareOverrideDrillResult = {
  available: boolean;
  authority: string;
  requestedDecision: SovereignXHardwareDecision;
  baselineDecision: SovereignXHardwareDecision;
  accepted: boolean;
  reason: string;
  driftFromBaseline: boolean;
  replayable: true;
  previewState: {
    currentFrequencyMhz: number;
    currentVoltageV: number;
    lastDecision: SovereignXHardwareDecision;
  };
  guardrails: string[];
};

export interface SovereignXHardwareOverrideDrillOptions {
  authority?: string;
}

const DEFAULT_AUTHORITY = 'SovereignX.Router';

export function runSovereignXHardwareOverrideDrill(
  snapshot: SovereignXHardwareSnapshot,
  request: SovereignXHardwareOverrideDrillRequest = {},
  options: SovereignXHardwareOverrideDrillOptions = {},
): SovereignXHardwareOverrideDrillResult {
  const authority = request.authority?.trim() || options.authority?.trim() || DEFAULT_AUTHORITY;
  const requestedDecision = request.requestedDecision ?? snapshot.cycle.decision;
  const reason = request.reason?.trim() || 'operator override drill';
  const accepted = authority === DEFAULT_AUTHORITY && reason.length > 0;
  const baselineDecision = snapshot.cycle.decision;
  const effectiveDecision = accepted ? requestedDecision : baselineDecision;
  const previewState = projectState(snapshot, effectiveDecision);

  return {
    available: true,
    authority,
    requestedDecision,
    baselineDecision,
    accepted,
    reason,
    driftFromBaseline: effectiveDecision !== baselineDecision,
    replayable: true,
    previewState,
    guardrails: accepted
      ? [
          'Authority matched the constitutional hardware router.',
          'The drill remains audit-only and does not mutate live hardware state.',
        ]
      : [
          'Authority must match the constitutional hardware router.',
          'The drill remains audit-only and does not mutate live hardware state.',
        ],
  };
}

function projectState(
  snapshot: SovereignXHardwareSnapshot,
  decision: SovereignXHardwareDecision,
): SovereignXHardwareOverrideDrillResult['previewState'] {
  const currentFrequencyMhz = snapshot.governor.state.currentFrequencyMhz;
  const currentVoltageV = snapshot.governor.state.currentVoltageV;

  switch (decision) {
    case 'PROMOTE':
      return {
        currentFrequencyMhz: Number((currentFrequencyMhz * 1.03).toFixed(3)),
        currentVoltageV: Number((currentVoltageV + 0.01).toFixed(3)),
        lastDecision: decision,
      };
    case 'RETRACT':
      return {
        currentFrequencyMhz: Number((currentFrequencyMhz * 0.97).toFixed(3)),
        currentVoltageV: Number(Math.max(0, currentVoltageV - 0.01).toFixed(3)),
        lastDecision: decision,
      };
    case 'QUARANTINE':
      return {
        currentFrequencyMhz: Number((currentFrequencyMhz * 0.95).toFixed(3)),
        currentVoltageV: Number((currentVoltageV * 0.98).toFixed(3)),
        lastDecision: decision,
      };
    case 'MAINTAIN':
    default:
      return {
        currentFrequencyMhz,
        currentVoltageV,
        lastDecision: 'MAINTAIN',
      };
  }
}
