import {
  createSovereignXHardwareGovernor,
  type SovereignXHardwareDecision,
} from '@aaes-os/sovereignx-router';

import type { SovereignXHardwareReplayRecord } from './sovereignxHardwareReplayStore.js';
import type { SovereignXHardwareSnapshot } from './SovereignXHardwareTelemetryAdapter.js';

export type SovereignXHardwareReplayValidationRow = {
  sequence: number;
  recordedAt: string;
  baselineDecision: SovereignXHardwareDecision;
  replayDecision: SovereignXHardwareDecision;
  decisionMatched: boolean;
  stateMatched: boolean;
  chaosDecisions: {
    kind: string;
    decision: SovereignXHardwareDecision;
    quarantined: boolean;
  }[];
};

export type SovereignXHardwareReplayValidationSummary = {
  available: boolean;
  storePath: string;
  recordCount: number;
  baselineMatches: number;
  baselineMismatches: number;
  chaosRuns: number;
  chaosQuarantines: number;
  passed: boolean;
  rows: SovereignXHardwareReplayValidationRow[];
};

export function validateSovereignXHardwareReplayRecords(
  records: SovereignXHardwareReplayRecord[],
  storePath: string,
): SovereignXHardwareReplayValidationSummary {
  if (records.length === 0) {
    return {
      available: false,
      storePath,
      recordCount: 0,
      baselineMatches: 0,
      baselineMismatches: 0,
      chaosRuns: 0,
      chaosQuarantines: 0,
      passed: false,
      rows: [],
    };
  }

  const rows = records.map((record) => validateRecord(record));
  const baselineMatches = rows.filter((row) => row.decisionMatched).length;
  const baselineMismatches = rows.length - baselineMatches;
  const chaosRuns = rows.reduce((sum, row) => sum + row.chaosDecisions.length, 0);
  const chaosQuarantines = rows.reduce((sum, row) => sum + row.chaosDecisions.filter((chaos) => chaos.quarantined).length, 0);

  return {
    available: true,
    storePath,
    recordCount: records.length,
    baselineMatches,
    baselineMismatches,
    chaosRuns,
    chaosQuarantines,
    passed: baselineMismatches === 0 && chaosQuarantines > 0,
    rows,
  };
}

function validateRecord(record: SovereignXHardwareReplayRecord): SovereignXHardwareReplayValidationRow {
  const previousState = record.snapshot.governor.previousState ?? record.snapshot.governor.state;
  const governor = createSovereignXHardwareGovernor({
    clock: () => previousState.lastUpdatedAtMs,
    initialFrequencyMhz: previousState.currentFrequencyMhz,
    initialVoltageV: previousState.currentVoltageV,
    authority: record.snapshot.governor.contract.Contract.Authority,
  });

  const replayCycle = governor.step(record.snapshot.telemetry);
  const chaosDecisions = buildChaosCases(record.snapshot, previousState).map((telemetry) => {
    const chaosGovernor = createSovereignXHardwareGovernor({
      clock: () => previousState.lastUpdatedAtMs,
      initialFrequencyMhz: previousState.currentFrequencyMhz,
      initialVoltageV: previousState.currentVoltageV,
      authority: record.snapshot.governor.contract.Contract.Authority,
    });
    const cycle = chaosGovernor.step(telemetry);
    return {
      kind: telemetry.observedAtMs === record.snapshot.telemetry.observedAtMs ? 'baseline-chaos' : telemetry.utilization > 1 ? 'utilization-chaos' : 'thermal-chaos',
      decision: cycle.decision,
      quarantined: cycle.decision === 'QUARANTINE',
    };
  });

  return {
    sequence: record.sequence,
    recordedAt: record.recordedAt,
    baselineDecision: record.snapshot.cycle.decision,
    replayDecision: replayCycle.decision,
    decisionMatched: replayCycle.decision === record.snapshot.cycle.decision,
    stateMatched: replayCycle.state.currentFrequencyMhz === record.snapshot.governor.state.currentFrequencyMhz
      && replayCycle.state.currentVoltageV === record.snapshot.governor.state.currentVoltageV
      && replayCycle.state.lastDecision === record.snapshot.governor.state.lastDecision,
    chaosDecisions,
  };
}

function buildChaosCases(
  snapshot: SovereignXHardwareSnapshot,
  previousState: SovereignXHardwareSnapshot['governor']['state'],
): SovereignXHardwareSnapshot['telemetry'][] {
  const baseline = snapshot.telemetry;
  return [
    {
      ...baseline,
      cpuTempC: baseline.cpuTempC + 20,
      gpuTempC: baseline.gpuTempC + 18,
      utilization: Math.min(1, baseline.utilization + 0.1),
      powerDrawFraction: Math.min(1, baseline.powerDrawFraction + 0.1),
      observedAtMs: baseline.observedAtMs ?? previousState.lastUpdatedAtMs,
    },
    {
      ...baseline,
      cpuVolt: baseline.cpuVolt + 0.25,
      gpuVolt: baseline.gpuVolt + 0.25,
      utilization: 1.2,
      observedAtMs: (baseline.observedAtMs ?? previousState.lastUpdatedAtMs) + 1,
    },
    {
      ...baseline,
      utilization: 0,
      powerDrawFraction: 0,
      observedAtMs: (baseline.observedAtMs ?? previousState.lastUpdatedAtMs) + 2,
    },
  ];
}
