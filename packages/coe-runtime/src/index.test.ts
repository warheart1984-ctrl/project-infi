import { describe, expect, it } from 'vitest';

import {
  createCoeRuntime,
  normalizeCoePromotionWorkflow,
  normalizeCoeRoute,
  normalizeCoeSchedule,
  validateCoePromotionWorkflow,
  validateCoeRoute,
  validateCoeSchedule,
} from './index.js';

const traceability = [
  {
    cisRequirement: 'COE-EXECUTION-001',
    referenceArchitecture: 'SOCK / COE',
    conformanceTest: 'packages/coe-runtime/src/index.test.ts',
    evidenceArtifact: 'coe-evidence-1',
  },
] as const;

describe('coe-runtime', () => {
  it('normalizes route, schedule, and promotion subjects deterministically', () => {
    const route = normalizeCoeRoute({
      intent: 'intent-1',
      agent: 'runtime-agent',
      policy: 'policy-1',
      decision: 'accept',
      pipeline: ['validate', 'execute'],
      traceability,
    });
    const schedule = normalizeCoeSchedule({
      workflow: 'release-promotion',
      triggers: ['receipt-ready'],
      constraints: ['replay-valid'],
      traceability,
    });
    const promotion = normalizeCoePromotionWorkflow({
      fromType: 'Prototype',
      toType: 'VerifiedPrototype',
      evidence: [{ id: 'receipt-1', kind: 'receipt' }],
      authority: { actor: 'alice', roles: ['steward'], permissions: ['promote'] },
      traceability,
    });

    expect(route.id).toHaveLength(64);
    expect(schedule.id).toHaveLength(64);
    expect(promotion.id).toHaveLength(64);
    expect(validateCoeRoute(route).valid).toBe(true);
    expect(validateCoeSchedule(schedule).valid).toBe(true);
    expect(validateCoePromotionWorkflow(promotion).valid).toBe(true);
  });

  it('rejects invalid execution subjects', () => {
    expect(
      validateCoeRoute({
        intent: '',
        agent: '',
        policy: '',
        decision: '',
        pipeline: [],
        traceability: [],
      }).issues.map((issue) => issue.field),
    ).toEqual(expect.arrayContaining(['intent', 'agent', 'policy', 'decision', 'pipeline', 'traceability']));

    expect(
      validateCoeSchedule({
        workflow: '',
        triggers: [],
        constraints: [],
        traceability: [],
      }).issues.map((issue) => issue.field),
    ).toEqual(expect.arrayContaining(['workflow', 'triggers', 'constraints', 'traceability']));
  });

  it('emits deterministic execution receipts and snapshots', () => {
    const runtime = createCoeRuntime();
    const routeReceipt = runtime.registerRoute({
      intent: 'intent-1',
      agent: 'runtime-agent',
      policy: 'policy-1',
      decision: 'accept',
      pipeline: ['validate', 'execute'],
      traceability,
    });
    const scheduleReceipt = runtime.schedule({
      workflow: 'release-promotion',
      triggers: ['receipt-ready'],
      constraints: ['replay-valid'],
      traceability,
    });
    const promotionReceipt = runtime.promote({
      fromType: 'Prototype',
      toType: 'VerifiedPrototype',
      evidence: [{ id: 'receipt-1', kind: 'receipt' }],
      authority: { actor: 'alice', roles: ['steward'], permissions: ['promote'] },
      traceability,
    });
    const rejectedReceipt = runtime.registerRoute({
      intent: '',
      agent: '',
      policy: '',
      decision: '',
      pipeline: [],
      traceability: [],
    });

    expect(routeReceipt.accepted).toBe(true);
    expect(scheduleReceipt.accepted).toBe(true);
    expect(promotionReceipt.accepted).toBe(true);
    expect(rejectedReceipt.accepted).toBe(false);
    expect(runtime.snapshot()).toMatchObject({
      packageName: '@aaes-os/coe-runtime',
      version: 'coe-v1',
      acceptedRoutes: 1,
      acceptedSchedules: 1,
      acceptedPromotions: 1,
      rejectedSubjects: 1,
      emittedReceipts: 4,
      lastReceiptId: rejectedReceipt.id,
    });
  });
});
