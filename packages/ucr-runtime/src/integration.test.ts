import { describe, expect, it } from 'vitest';

import {
  FaultJournal,
  GovernanceHub,
  PatternLedger,
} from '@aaes-os/aaes-governance';
import { TraceBus } from '@aaes-os/trace-bus';
import { UCRRuntime } from './ucrRuntime.js';

describe('UCRRuntime governance hub integration', () => {
  it('records invariant faults and emits trace events for string output', async () => {
    const traceBus = new TraceBus();
    const journal = new FaultJournal();
    const patternLedger = new PatternLedger();
    const hub = new GovernanceHub({ journal, patternLedger, traceBus });

    const runtime = new UCRRuntime({
      traceBus,
      faultJournal: journal,
      outputMode: 'string',
      enablePatches: false,
    });

    const result = await runtime.run({ kind: 'test', payload: { x: 1 } });

    expect(result.faults.length).toBeGreaterThan(0);
    expect(result.faults.some((f) => f.faultCode.includes('INV_OUTPUT_SHAPE'))).toBe(true);

    expect(patternLedger.getAll().length).toBeGreaterThan(0);

    const traceLog = traceBus.getLog();
    expect(traceLog.some((e) => e.type === 'TRACE_FAULT')).toBe(true);
    expect(traceLog.some((e) => e.type === 'TRACE_INVARIANT')).toBe(true);
    expect(traceLog.some((e) => e.type === 'TRACE_RUN_START')).toBe(true);

    hub.dispose();
  });
});
