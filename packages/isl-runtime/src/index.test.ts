import { describe, expect, it } from 'vitest';

import { createIslRuntime, normalizeIslIntent, validateIslIntent } from './index.js';

const sampleIntent = {
  actor: '  alice  ',
  target: ' sovereign/kernel ',
  purpose: ' establish governed execution ',
  context: {
    stage: '  release ',
    layers: [' CSL ', ' ISL '],
  },
  evidence: [
    {
      id: ' evidence-1 ',
      kind: ' receipt ',
      uri: ' file:///tmp/evidence-1.json ',
    },
  ],
  authority: {
    actor: ' alice ',
    roles: [' steward ', ' reviewer '],
    permissions: [' submit-intent ', ' approve-intent '],
  },
  traceability: [
    {
      cisRequirement: ' CIS-INTENT-001 ',
      referenceArchitecture: ' Reference Architecture / ISL ',
      conformanceTest: ' tests/isl-runtime.test.ts ',
      evidenceArtifact: ' evidence-isl-001 ',
    },
  ],
} as const;

describe('isl-runtime', () => {
  it('normalizes and hashes governed intents deterministically', () => {
    const intent = normalizeIslIntent(sampleIntent);

    expect(intent.actor).toBe('alice');
    expect(intent.target).toBe('sovereign/kernel');
    expect(intent.purpose).toBe('establish governed execution');
    expect(intent.id).toHaveLength(64);
    expect(validateIslIntent(intent).valid).toBe(true);
  });

  it('reports missing evidence and authority as invalid', () => {
    const result = validateIslIntent({
      actor: 'alice',
      target: 'kernel',
      purpose: 'test',
      context: {},
      evidence: [],
      authority: { actor: '', roles: [], permissions: [] },
      traceability: [],
    });

    expect(result.valid).toBe(false);
    expect(result.issues.map((issue) => issue.field)).toEqual(
      expect.arrayContaining(['evidence', 'authority.actor', 'authority.roles', 'traceability']),
    );
  });

  it('tracks accepted and rejected intents in the runtime snapshot', () => {
    const runtime = createIslRuntime();
    const accepted = runtime.submitIntent(sampleIntent);
    const rejected = runtime.submitIntent({
      actor: 'alice',
      target: '',
      purpose: 'test',
      context: {},
      evidence: [],
      authority: { actor: 'alice', roles: [], permissions: [] },
      traceability: [],
    });

    expect(accepted.accepted).toBe(true);
    expect(rejected.accepted).toBe(false);

    const snapshot = runtime.snapshot();
    expect(snapshot.packageName).toBe('@aaes-os/isl-runtime');
    expect(snapshot.acceptedIntents).toBe(1);
    expect(snapshot.rejectedIntents).toBe(1);
    expect(snapshot.totalIntents).toBe(2);
    expect(snapshot.lastIntentId).toBe(accepted.intent.id);
  });
});
