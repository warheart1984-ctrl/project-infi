import { describe, expect, it } from 'vitest';

import { buildCicRuleHash, createCicRuntime, evaluateCicRule, normalizeCicRule, validateCicRule } from './index.js';

const sampleRule = {
  id: 'receipt-is-release-evidence',
  conditions: [
    { path: 'artifact.kind', operator: '=', value: 'receipt' },
    { path: 'artifact.tier', operator: '>=', value: 1 },
  ],
  conclusion: 'artifact qualifies as release evidence',
  bindings: [
    {
      artifactField: 'ConstitutionalReceipt.receiptId',
      semanticConcept: 'release.evidence.receipt',
    },
  ],
  traceability: [
    {
      cisRequirement: 'CIC-INFERENCE-001',
      referenceArchitecture: 'SOCK / CIC',
      conformanceTest: 'packages/cic-runtime/src/index.test.ts',
      evidenceArtifact: 'cic-evidence-1',
    },
  ],
} as const;

describe('cic-runtime', () => {
  it('normalizes and hashes inference rules deterministically', () => {
    const rule = normalizeCicRule(sampleRule);

    expect(rule.id).toBe('receipt-is-release-evidence');
    expect(rule.hash).toHaveLength(64);
    expect(rule.hash).toBe(buildCicRuleHash(sampleRule));
    expect(validateCicRule(rule).valid).toBe(true);
  });

  it('evaluates matching and non-matching conditions deterministically', () => {
    const matched = evaluateCicRule(sampleRule, { artifact: { kind: 'receipt', tier: 2 } });
    const missed = evaluateCicRule(sampleRule, { artifact: { kind: 'note', tier: 2 } });

    expect(matched.matched).toBe(true);
    expect(matched.conclusion).toBe('artifact qualifies as release evidence');
    expect(matched.bindings).toHaveLength(1);
    expect(missed.matched).toBe(false);
    expect(missed.conclusion).toBeUndefined();
  });

  it('rejects malformed rules and missing traceability', () => {
    const result = validateCicRule({
      id: '',
      conditions: [],
      conclusion: '',
      bindings: [{ artifactField: '', semanticConcept: '' }],
      traceability: [],
    });

    expect(result.valid).toBe(false);
    expect(result.issues.map((issue) => issue.field)).toEqual(
      expect.arrayContaining(['id', 'conditions', 'conclusion', 'bindings[0].artifactField', 'bindings[0].semanticConcept', 'traceability']),
    );
  });

  it('builds semantic graphs and tracks runtime snapshots', () => {
    const runtime = createCicRuntime([sampleRule]);
    const rejected = runtime.registerRule({
      id: '',
      conditions: [],
      conclusion: '',
      bindings: [],
      traceability: [],
    });
    const graph = runtime.infer({ artifact: { kind: 'receipt', tier: 1 } });

    expect(rejected.accepted).toBe(false);
    expect(graph.id).toHaveLength(64);
    expect(graph.matchedRuleIds).toEqual(['receipt-is-release-evidence']);
    expect(graph.conclusions).toEqual(['artifact qualifies as release evidence']);
    expect(runtime.snapshot()).toMatchObject({
      packageName: '@aaes-os/cic-runtime',
      version: 'cic-v1',
      totalRules: 2,
      acceptedRules: 1,
      rejectedRules: 1,
      totalInferences: 1,
      lastRuleId: 'receipt-is-release-evidence',
      lastGraphId: graph.id,
    });
  });
});
