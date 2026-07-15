import { describe, expect, it } from 'vitest';

import { buildCccContinuityId, createCccRuntime, normalizeCccContinuity, replayCccContinuity, validateCccContinuity } from './index.js';

const sampleContinuity = {
  invariant: 'release evidence chain remains replayable',
  scope: 'sovereign/runtime-spine',
  replayContract: {
    mode: 'historical',
    deterministic: true,
    ledgerReferences: [{ id: 'ledger-1', kind: 'receipt', uri: 'file:///tmp/ledger-1.json' }],
  },
  timeline: {
    events: ['intent submitted', 'inference accepted', 'execution scheduled'],
    states: ['draft', 'verified'],
    transitions: ['draft->verified'],
  },
  traceability: [
    {
      cisRequirement: 'CCC-CONTINUITY-001',
      referenceArchitecture: 'SOCK / CCC',
      conformanceTest: 'packages/ccc-runtime/src/index.test.ts',
      evidenceArtifact: 'ccc-evidence-1',
    },
  ],
} as const;

describe('ccc-runtime', () => {
  it('normalizes and hashes continuity contracts deterministically', () => {
    const continuity = normalizeCccContinuity(sampleContinuity);

    expect(continuity.invariant).toBe('release evidence chain remains replayable');
    expect(continuity.id).toHaveLength(64);
    expect(continuity.id).toBe(buildCccContinuityId(sampleContinuity));
    expect(validateCccContinuity(continuity).valid).toBe(true);
  });

  it('rejects non-replayable continuity contracts', () => {
    const result = validateCccContinuity({
      invariant: '',
      scope: '',
      replayContract: {
        mode: 'historical',
        deterministic: true,
        ledgerReferences: [],
      },
      timeline: {
        events: [],
        states: ['only-state'],
        transitions: ['only-state->missing'],
      },
      traceability: [],
    });

    expect(result.valid).toBe(false);
    expect(result.issues.map((issue) => issue.field)).toEqual(
      expect.arrayContaining([
        'invariant',
        'scope',
        'replayContract.ledgerReferences',
        'timeline.events',
        'timeline.transitions',
        'traceability',
      ]),
    );
  });

  it('emits deterministic replay evidence', () => {
    const first = replayCccContinuity(sampleContinuity);
    const second = replayCccContinuity(sampleContinuity);

    expect(first.accepted).toBe(true);
    expect(first.replayId).toBe(second.replayId);
    expect(first.timelineHash).toHaveLength(64);
    expect(first.ledgerHash).toHaveLength(64);
  });

  it('tracks accepted, rejected, and replayed continuities', () => {
    const runtime = createCccRuntime();
    const accepted = runtime.registerContinuity(sampleContinuity);
    const rejected = runtime.registerContinuity({
      invariant: '',
      scope: '',
      replayContract: { mode: 'comparison', deterministic: true, ledgerReferences: [] },
      timeline: { events: [], states: [], transitions: [] },
      traceability: [],
    });
    const replay = runtime.replay(accepted.continuity);

    expect(accepted.accepted).toBe(true);
    expect(rejected.accepted).toBe(false);
    expect(runtime.snapshot()).toMatchObject({
      packageName: '@aaes-os/ccc-runtime',
      version: 'ccc-v1',
      totalContinuities: 2,
      acceptedContinuities: 1,
      rejectedContinuities: 1,
      totalReplays: 1,
      lastContinuityId: accepted.continuity.id,
      lastReplayId: replay.replayId,
    });
  });
});
