import { describe, expect, it } from 'vitest';

import { DefaultUCRRuntime } from '@aaes-os/ucr-runtime';
import { TRACE_FAULT } from '@aaes-os/trace-bus';

describe('invariant engine integration', () => {
  it('wires UCRRuntime.run() through runledger, governance, and trace-bus', async () => {
    const runtime = new DefaultUCRRuntime({ enablePatches: false, demoSchedule: ['string'] });
    const result = await runtime.run({ kind: 'demo', payload: { task: 'demo' }, runIndex: 0 });

    expect(result.faults.map((fault) => fault.faultCode)).toEqual(
      expect.arrayContaining([expect.stringMatching(/INV_OUTPUT_SHAPE/)]),
    );
    expect(result.runId).toBeDefined();
  });

  it('emits TRACE_FAULT on invariant breach', async () => {
    const runtime = new DefaultUCRRuntime({ enablePatches: false, demoSchedule: ['random'] });
    await runtime.run({ kind: 'demo', runIndex: 0 });

    const faults = runtime
      .getTraceBus()
      .getLog()
      .filter((event) => event.type === TRACE_FAULT);
    expect(faults.length).toBeGreaterThan(0);
    expect(faults[0]?.fault?.faultCode).toMatch(/INV_FAIL_/);
  });
});
