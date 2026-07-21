import { describe, expect, it } from 'vitest';

import {
  createSovereignXHardwareGovernor,
  sovereignXHardwareGovernanceContract,
  validateSovereignXHardwareGovernanceContract,
  type SovereignXHardwareTelemetry,
} from './index.ts';

const stableTelemetry: SovereignXHardwareTelemetry = {
  cpuTempC: 68,
  gpuTempC: 69,
  cpuVolt: 1.08,
  gpuVolt: 1.08,
  powerDrawFraction: 0.62,
  utilization: 0.45,
  utilizationSamples: [
    { atMs: 1_700_000_000_000 - 150, utilization: 0.82 },
    { atMs: 1_700_000_000_000 - 50, utilization: 0.86 },
  ],
  observedAtMs: 1_700_000_000_000,
};

describe('SovereignX hardware governor', () => {
  it('validates the constitutional hardware contract', () => {
    const validation = validateSovereignXHardwareGovernanceContract(sovereignXHardwareGovernanceContract);

    expect(validation.passed).toBe(true);
    expect(validation.issues).toHaveLength(0);
  });

  it('promotes and retracts when headroom and utilization justify a burst', () => {
    const governor = createSovereignXHardwareGovernor({
      clock: () => 1_700_000_000_000,
      initialFrequencyMhz: 3_600,
      initialVoltageV: 1.1,
    });

    const cycle = governor.step(stableTelemetry);

    expect(cycle.decision).toBe('PROMOTE');
    expect(cycle.transitions).toHaveLength(2);
    expect(cycle.transitions[0]?.kind).toBe('PROMOTE');
    expect(cycle.transitions[1]?.kind).toBe('RETRACT');
    expect(cycle.transitions[0]?.replayable).toBe(true);
    expect(cycle.transitions[0]?.telemetryHash).toBe(cycle.transitions[1]?.telemetryHash);
    expect(cycle.state.lastDecision).toBe('RETRACT');
    expect(cycle.state.currentFrequencyMhz).toBeLessThan(3_600);
    expect(governor.listEvents()).toHaveLength(2);
  });

  it('quarantines invalid telemetry and records a replayable evidence trail', () => {
    const governor = createSovereignXHardwareGovernor({ clock: () => 1_700_000_000_500 });
    const cycle = governor.step({
      cpuTempC: 92,
      gpuTempC: 88,
      cpuVolt: 1.05,
      gpuVolt: 1.05,
      powerDrawFraction: 0.7,
      utilization: 0.9,
      observedAtMs: 1_700_000_000_500,
    });

    expect(cycle.decision).toBe('QUARANTINE');
    expect(cycle.evidence.valid).toBe(false);
    expect(cycle.transitions).toHaveLength(1);
    expect(cycle.transitions[0]?.kind).toBe('QUARANTINE');
    expect(cycle.transitions[0]?.reason).toContain('validation');
    expect(governor.listEvents()).toHaveLength(1);
  });

  it('maintains current state when the constitutional thresholds are not crossed', () => {
    const governor = createSovereignXHardwareGovernor({
      clock: () => 1_700_000_000_000,
      initialFrequencyMhz: 3_400,
      initialVoltageV: 1.0,
    });

    const cycle = governor.step({
      cpuTempC: 70,
      gpuTempC: 71,
      cpuVolt: 1.02,
      gpuVolt: 1.02,
      powerDrawFraction: 0.55,
      utilization: 0.32,
      observedAtMs: 1_700_000_000_000,
    });

    expect(cycle.decision).toBe('MAINTAIN');
    expect(cycle.transitions).toHaveLength(1);
    expect(cycle.transitions[0]?.kind).toBe('MAINTAIN');
    expect(cycle.state.currentFrequencyMhz).toBe(3_400);
    expect(cycle.state.currentVoltageV).toBe(1.0);
  });
});
