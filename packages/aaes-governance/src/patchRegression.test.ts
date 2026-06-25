import { describe, expect, it, beforeEach } from 'vitest';

import { FaultJournal } from './faultJournal.js';
import { createMinimalInvariantEngine } from './governanceHub.js';
import { FAULT_CODE_SPAN_ORPHAN } from './faultCodes.js';
import { clearPatchGlobals, seedApprovedPatches } from '@aaes-os/tri-core-protocol';
import { UCRRuntime } from '@aaes-os/ucr-runtime';

describe('patch regression (constitutional patches)', () => {
  beforeEach(() => {
    clearPatchGlobals();
  });

  it('INV_OUTPUT_SHAPE: string output fails before patch, passes after PATCH_OUTPUT_SHAPE_001', async () => {
    const journal = new FaultJournal();
    const { engine } = createMinimalInvariantEngine(journal);

    const before = new UCRRuntime({
      enablePatches: false,
      demoSchedule: ['string'],
      faultJournal: journal,
      invariantEngine: engine,
    });
    await before.run({ payload: 'hello' });
    expect(journal.getAll().some((f) => f.faultCode.includes('INV_OUTPUT_SHAPE'))).toBe(true);

    journal.clear();
    seedApprovedPatches();
    const after = new UCRRuntime({
      enablePatches: true,
      demoSchedule: ['string'],
      faultJournal: journal,
      invariantEngine: engine,
    });
    await after.run({ payload: 'hello' });
    expect(journal.getAll().some((f) => f.faultCode.includes('INV_OUTPUT_SHAPE'))).toBe(false);
  });

  it('INV_DETERMINISM: random field fails before patch, passes after PATCH_DETERMINISM_001', async () => {
    const journal = new FaultJournal();
    const { engine } = createMinimalInvariantEngine(journal);

    const before = new UCRRuntime({
      enablePatches: false,
      demoSchedule: ['random'],
      faultJournal: journal,
      invariantEngine: engine,
    });
    await before.run({ payload: {} });
    expect(journal.getAll().some((f) => f.faultCode.includes('INV_DETERMINISM'))).toBe(true);

    journal.clear();
    seedApprovedPatches();
    const after = new UCRRuntime({
      enablePatches: true,
      demoSchedule: ['random'],
      faultJournal: journal,
      invariantEngine: engine,
    });
    await after.run({ payload: {} });
    expect(journal.getAll().some((f) => f.faultCode.includes('INV_DETERMINISM'))).toBe(false);
  });

  it('SPAN_BOUNDARY: orphan span fault before patch, clean close after PATCH_SPAN_BOUNDARY_001', async () => {
    const journal = new FaultJournal();
    const { engine } = createMinimalInvariantEngine(journal);

    const before = new UCRRuntime({
      enablePatches: false,
      demoSchedule: ['throw'],
      faultJournal: journal,
      invariantEngine: engine,
    });
    const beforeResult = await before.run({ payload: {} });
    expect(beforeResult.status).toBe('failed');
    expect(beforeResult.spanOrphan).toBe(true);
    expect(journal.getAll().some((f) => f.faultCode === FAULT_CODE_SPAN_ORPHAN)).toBe(true);

    journal.clear();
    seedApprovedPatches();
    const after = new UCRRuntime({
      enablePatches: true,
      demoSchedule: ['throw'],
      faultJournal: journal,
      invariantEngine: engine,
    });
    const afterResult = await after.run({ payload: {} });
    expect(afterResult.status).toBe('failed');
    expect(afterResult.spanOrphan).toBe(false);
    expect(journal.getAll().some((f) => f.faultCode === FAULT_CODE_SPAN_ORPHAN)).toBe(false);
  });
});
