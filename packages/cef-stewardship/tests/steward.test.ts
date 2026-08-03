import { describe, expect, it } from 'vitest';
import { stewardEvidence } from '../src/index.js';

const holdEvidence = {
  id: 'evidence-steward-001',
  type: 'OEL',
  version: '1.0.0',
  authority: { carId: 'car-ops-001', actorId: 'a', role: 'approver' },
  context: { domain: 'ops' },
  inputs: {},
  verification: { checks: [{ id: 'check-audit', result: 'passed' }] },
  lineage: {},
  replay: { instructions: 'replay' },
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
      netpol: 'p',
      rbac: 'p',
      securityContext: 'p',
    },
  },
};

describe('stewardEvidence', () => {
  it('returns DRAFT stewardship for hold baseline evidence', () => {
    const record = stewardEvidence('OEL', holdEvidence, 'evidence-steward-001');
    expect(record.profileValid).toBe(true);
    expect(record.certificate.status).toBe('DRAFT');
    expect(record.nextActions.some((a) => /DRAFT/i.test(a))).toBe(true);
  });
});
