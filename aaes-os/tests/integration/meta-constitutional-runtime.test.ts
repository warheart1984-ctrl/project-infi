import { describe, expect, it } from 'vitest';

import {
  buildMRIOutputV2,
  PILOT_AFTER,
  PILOT_BEFORE,
  runMRIComparison,
} from '@aaes-os/mri-instrument';
import {
  ConstitutionalEnforcementNode,
  compileInvariantDsl,
} from '@aaes-os/constitutional-enforcement-node';
import { recordMetaConstitutionalCollapsePod } from '@aaes-os/meta-constitutional-calculus';

describe('meta constitutional runtime integration', () => {
  it('routes MRI v0.2 state through CEN and records the meta-collapse POD', () => {
    const mri = buildMRIOutputV2(runMRIComparison(PILOT_BEFORE, PILOT_AFTER), {
      industryAverage: { continuity: 61, governance: 59, memory: 64, coordination: 57, confidence: 70 },
      topQuartile: { continuity: 78, governance: 74, memory: 82, coordination: 71, confidence: 85 },
      previousMeasurement: { continuity: 64, governance: 72, memory: 64, coordination: 65, confidence: 74 },
    });
    const cen = new ConstitutionalEnforcementNode({
      invariants: [compileInvariantDsl('require confidence >= 70')],
    });

    const enforcement = cen.execute({
      transitionId: 'transition:proof-1-to-cml-15',
      transitionType: 'law_mutation',
      payload: { podId: 'meta_constitutional_collapse' },
      requestedCapabilities: ['law:propose'],
      context: {
        actor: 'jon halstead sigil 1001',
        mriSnapshot: mri.state_vector,
        runtimeContext: {
          corridorId: 'law-evolution',
          capabilities: ['law:propose'],
        },
      },
    });
    const pod = recordMetaConstitutionalCollapsePod();

    expect(enforcement.decision.verdict).toBe('ALLOW');
    expect(enforcement.receipt.mriSnapshotHash).toMatch(/^sha3-256:/);
    expect(pod.status).toBe('recorded');
    expect(pod.receipt.kind).toBe('generic');
  });
});
