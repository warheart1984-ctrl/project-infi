import type { CefEvidence } from '../src/types/Evidence.js';

export function validCoreEvidence(
  overrides: Partial<CefEvidence> = {},
): CefEvidence {
  return {
    id: 'evidence-test-001',
    type: 'OEL',
    version: '1.0.0',
    authority: {
      carId: 'car-ops-001',
      actorId: 'ops-approver-001',
      role: 'approver',
    },
    context: {
      domain: 'ops',
      subdomain: 'test',
    },
    inputs: {
      artifacts: ['example.md'],
      dataRefs: [],
      advisoryOutputs: [],
    },
    verification: {
      checks: [{ id: 'check-audit', result: 'passed' }],
    },
    lineage: {
      parentEvidence: null,
      previousVersions: [],
    },
    replay: {
      instructions: 'checkout commit; re-run validation; compare results',
    },
    audit: {
      visibility: 'internal',
      disclosure: [],
    },
    promotion: {
      decision: 'hold',
      signature: null,
      timestamp: null,
    },
    ...overrides,
  };
}

export function validOelEvidence(
  overrides: Partial<CefEvidence> = {},
): CefEvidence {
  return validCoreEvidence({
    type: 'OEL',
    oel: {
      deploymentId: 'aaes-os-production-baseline-v1.0',
      commitSha: '7efa0c5f766bc0b30b6eef820d198be3a6bf1a5d',
      containerDigest: 'pending',
      immutableTag: 'pending',
      sbomRef: 'pending',
      supplyChainFacts: { status: 'pending' },
      vulnerabilityScan: { tool: 'trivy', status: 'pending' },
      securityGates: { status: 'pending' },
      conformanceTests: { passed: 0, total: 0 },
      runtimeHealth: { status: 'pending' },
      policyValidation: {
        netpol: 'pending',
        rbac: 'pending',
        securityContext: 'pending',
      },
    },
    ...overrides,
  });
}

export function validCrecEvidence(
  overrides: Partial<CefEvidence> = {},
): CefEvidence {
  return validCoreEvidence({
    type: 'CREC',
    context: { domain: 'research', subdomain: 'crec-fixture' },
    crec: {
      experimentId: 'exp-001',
      claim: 'Fixture claim bounded by methods and results',
      methods: ['unit-test'],
      results: { status: 'fixture' },
      proofSurfaceLevel: 'P1',
    },
    ...overrides,
  });
}

export function validCelEvidence(
  overrides: Partial<CefEvidence> = {},
): CefEvidence {
  return validCoreEvidence({
    type: 'CEL',
    context: { domain: 'language', subdomain: 'cel-fixture' },
    cel: {
      expression: 'ja ema',
      compilerVersion: '0.3.0',
      isf: { version: '0.4' },
      invariantsPassed: true,
    },
    ...overrides,
  });
}

export function validSecurityEvidence(
  overrides: Partial<CefEvidence> = {},
): CefEvidence {
  return validCoreEvidence({
    type: 'Security',
    context: { domain: 'security', subdomain: 'security-fixture' },
    security: {
      sbomRef: 'sbom:fixture',
      vulnerabilityScan: { tool: 'trivy', status: 'pending' },
      supplyChain: { status: 'pending' },
      policyGates: { status: 'pending' },
      overallStatus: 'PENDING',
    },
    ...overrides,
  });
}

export function validModelEvalEvidence(
  overrides: Partial<CefEvidence> = {},
): CefEvidence {
  return validCoreEvidence({
    type: 'ModelEval',
    context: { domain: 'model', subdomain: 'modeleval-fixture' },
    modelEval: {
      modelId: 'model-fixture-001',
      benchmarkSuite: 'fixture-suite',
      scores: { accuracy: 0 },
      riskAssessment: { level: 'unknown' },
      uncertainty: { method: 'none' },
    },
    ...overrides,
  });
}
