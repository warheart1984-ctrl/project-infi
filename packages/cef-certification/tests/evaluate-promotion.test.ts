import { describe, expect, it } from 'vitest';
import { evaluatePromotion } from '../src/index.js';

const holdEvidence = {
  id: 'evidence-cert-001',
  type: 'OEL',
  version: '1.0.0',
  authority: { carId: 'car-ops-001', actorId: 'a', role: 'approver' },
  context: { domain: 'ops' },
  inputs: {},
  verification: {
    checks: [{ id: 'check-security', result: 'pending' }],
  },
  lineage: {},
  replay: { instructions: 'replay steps' },
  audit: { visibility: 'internal' },
  promotion: { decision: 'hold', signature: null, timestamp: null },
  oel: {
    deploymentId: 'd1',
    commitSha: '7efa0c5f766bc0b30b6eef820d198be3a6bf1a5d',
    containerDigest: 'pending',
    immutableTag: 'pending',
    sbomRef: 'pending',
    supplyChainFacts: {},
    vulnerabilityScan: {},
    securityGates: {},
    conformanceTests: { passed: 0, total: 0 },
    runtimeHealth: {},
    policyValidation: {
      netpol: 'pending',
      rbac: 'pending',
      securityContext: 'pending',
    },
  },
};

describe('evaluatePromotion', () => {
  it('keeps HOLD evidence as DRAFT', () => {
    const cert = evaluatePromotion('OEL', holdEvidence, 'evidence-cert-001');
    expect(cert.status).toBe('DRAFT');
    expect(cert.stewardshipState).toBe('unpromoted');
  });

  it('refuses ACTIVE when approved but checks pending', () => {
    const bad = {
      ...holdEvidence,
      promotion: {
        decision: 'approved',
        signature: 'sig',
        timestamp: '2026-07-31T21:00:00.000Z',
      },
    };
    const cert = evaluatePromotion('OEL', bad, 'evidence-cert-001');
    expect(cert.status).toBe('DRAFT');
    expect(cert.reason).toMatch(/pending/i);
  });
});
