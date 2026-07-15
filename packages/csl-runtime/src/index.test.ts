import { describe, expect, it } from 'vitest';

import { buildCslArtifactId, createCslRuntime, normalizeCslArtifactType, validateCslArtifactType } from './index.js';

const sampleArtifact = {
  name: 'ConstitutionalReceipt',
  tier: 1,
  kind: 'receipt',
  fields: [
    { name: 'receiptId', type: 'string', required: true },
    { name: 'artifactId', type: 'string', required: true },
    { name: 'hash', type: 'string' },
  ],
  dynamics: {
    generates: ['EvidenceBundle'],
    resolves: ['ReleaseClaim'],
  },
  horizon: {
    promotesTo: 'ReleaseVerified',
    expandsTo: ['ReplayReceipt'],
  },
  traceability: [
    {
      cisRequirement: 'CSL-ARTIFACT-001',
      referenceArchitecture: 'SOCK / CSL',
      conformanceTest: 'packages/csl-runtime/src/index.test.ts',
      evidenceArtifact: 'csl-evidence-1',
    },
  ],
} as const;

describe('csl-runtime', () => {
  it('normalizes and hashes constitutional artifact schemas deterministically', () => {
    const artifact = normalizeCslArtifactType({
      ...sampleArtifact,
      fields: [...sampleArtifact.fields].reverse(),
    });

    expect(artifact.name).toBe('ConstitutionalReceipt');
    expect(artifact.fields.map((field) => field.name)).toEqual(['artifactId', 'hash', 'receiptId']);
    expect(artifact.id).toHaveLength(64);
    expect(artifact.id).toBe(buildCslArtifactId(sampleArtifact));
    expect(validateCslArtifactType(artifact).valid).toBe(true);
  });

  it('rejects malformed schemas and missing traceability', () => {
    const result = validateCslArtifactType({
      name: '1bad name',
      tier: -1,
      kind: '',
      fields: [
        { name: '', type: '' },
        { name: '', type: 'string' },
      ],
      dynamics: {},
      horizon: { promotesTo: '' },
      traceability: [],
    });

    expect(result.valid).toBe(false);
    expect(result.issues.map((issue) => issue.field)).toEqual(
      expect.arrayContaining([
        'name',
        'tier',
        'kind',
        'fields[0].name',
        'fields[0].type',
        'fields[1].name',
        'horizon.promotesTo',
        'traceability',
      ]),
    );
  });

  it('tracks accepted and rejected artifact schemas', () => {
    const runtime = createCslRuntime();
    const accepted = runtime.registerArtifact(sampleArtifact);
    const rejected = runtime.registerArtifact({
      name: '',
      tier: 0,
      kind: '',
      fields: [],
      dynamics: {},
      horizon: { promotesTo: '' },
      traceability: [],
    });

    expect(accepted.accepted).toBe(true);
    expect(rejected.accepted).toBe(false);
    expect(runtime.findArtifact('constitutional receipt')).toMatchObject({ id: accepted.artifact.id });
    expect(runtime.snapshot()).toMatchObject({
      packageName: '@aaes-os/csl-runtime',
      version: 'csl-v1',
      totalArtifacts: 2,
      acceptedArtifacts: 1,
      rejectedArtifacts: 1,
      lastArtifactId: accepted.artifact.id,
    });
  });
});
