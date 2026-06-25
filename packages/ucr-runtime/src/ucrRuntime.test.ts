import { describe, expect, it } from 'vitest';

import { TRACE_FAULT } from '@aaes-os/trace-bus';

import { DefaultUCRRuntime } from './ucrRuntime.js';

describe('DefaultUCRRuntime integration', () => {
  it('records faults and trace events for bad output with recurrence on repeated runs', async () => {
    const runtime = new DefaultUCRRuntime({ enablePatches: false, demoSchedule: ['string'] });
    const bus = runtime.getTraceBus();

    const first = await runtime.run({ kind: 'demo', payload: { x: 1 }, runIndex: 0 });
    const second = await runtime.run({ kind: 'demo', payload: { x: 1 }, runIndex: 0 });

    expect(first.faults.length).toBeGreaterThanOrEqual(1);
    expect(second.faults.length).toBeGreaterThanOrEqual(1);
    expect(first.faults.some((f) => f.faultCode.includes('INV_OUTPUT_SHAPE'))).toBe(true);
    expect(first.faults[0]?.recurrenceCount).toBe(1);
    expect(second.faults[0]?.recurrenceCount).toBe(2);

    const faultEvents = bus.getLog().filter((event) => event.type === TRACE_FAULT);
    expect(faultEvents.length).toBeGreaterThanOrEqual(2);
  });

  it('passes invariants for good demo schedule', async () => {
    const runtime = new DefaultUCRRuntime({ enablePatches: false, demoSchedule: ['good'] });
    const result = await runtime.run({ kind: 'demo', payload: { ok: true }, runIndex: 0 });

    expect(result.output).toEqual({ echo: { ok: true } });
    expect(result.faults).toHaveLength(0);
  });

  it('records determinism faults for random demo schedule', async () => {
    const runtime = new DefaultUCRRuntime({ enablePatches: false, demoSchedule: ['random'] });
    const result = await runtime.run({ kind: 'demo', runIndex: 0 });

    expect(result.faults.some((fault) => fault.faultCode.includes('DETERMINISM'))).toBe(true);
  });
});
