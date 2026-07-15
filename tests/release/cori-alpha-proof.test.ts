import { readFileSync } from 'node:fs';
import path from 'node:path';
import { describe, expect, it } from 'vitest';

function releasePath(fileName: string): string {
  return path.join(process.cwd(), 'docs', 'crk1', 'release', fileName);
}

function readReleaseText(fileName: string): string {
  return readFileSync(releasePath(fileName), 'utf8');
}

function readReleaseJson<T>(fileName: string): T {
  return JSON.parse(readReleaseText(fileName)) as T;
}

describe('CORI Alpha proof chain', () => {
  it('binds the proof chain to the generated conformance input and traceability matrix', () => {
    const hierarchy = readReleaseJson<{
      traceabilityMatrix: Array<{ requirement: string; component: string; evidence: string[]; test: string }>;
    }>('CIS_STANDARDS_HIERARCHY.spec.json');
    const conformanceInput = readReleaseJson<{
      status: string;
      generatedFrom: string;
      traceabilityPath: string[];
      requirements: Array<{ id: string; requirement: string; component: string; evidence: string[]; tests: string[] }>;
      validationFamilies: Array<{ id: string; name: string; purpose: string; acceptanceCriteria: string[] }>;
      acceptanceCriteria: string[];
    }>('CIS_CONFORMANCE_SUITE_INPUT.spec.json');
    const proofChain = readReleaseText('CORI_ALPHA_PROOF_CHAIN.md');

    expect(conformanceInput.status).toBe('Frozen');
    expect(conformanceInput.generatedFrom).toBe('cis-standards-hierarchy');
    expect(conformanceInput.traceabilityPath).toEqual([
      'Architecture',
      'Ontology',
      'Knowledge Graph',
      'GKS',
      'Research OS',
      'Reference Runtime',
      'Conformance',
      'Evidence',
      'Replay',
      'External Standards',
    ]);
    expect(conformanceInput.requirements).toHaveLength(hierarchy.traceabilityMatrix.length);
    expect(conformanceInput.requirements.at(-1)).toMatchObject({
      id: 'CR-10',
      requirement: 'CORI Alpha is the first independently verifiable constitutional proof',
      component: 'CORI_ALPHA_PROOF_CHAIN.md',
    });
    expect(conformanceInput.validationFamilies.map((family) => family.id)).toEqual([
      'VF-1',
      'VF-2',
      'VF-3',
      'VF-4',
      'VF-5',
    ]);
    expect(conformanceInput.acceptanceCriteria).toEqual([
      'The suite remains synchronized with the traceability matrix.',
      'The suite input remains machine-readable and replayable.',
      'The suite produces evidence-first outcomes only.',
      'The suite identifies blocking gaps instead of overstating readiness.',
    ]);

    expect(proofChain).toContain('first constitutional proof milestone');
    expect(proofChain).toContain('Constitutional Receipt');
    expect(proofChain).toContain('replay');
    expect(proofChain).toContain('conformance');
    expect(proofChain).toContain('evidence package');
    expect(proofChain).toContain('governed proof milestone');
  });

  it('keeps the proof chain independently verifiable through receipts, replay, and conformance', () => {
    const matrix = readReleaseText('CIS_STANDARDS_TRACEABILITY_MATRIX.md');
    const hierarchyDoc = readReleaseText('CIS_STANDARDS_HIERARCHY.md');

    expect(matrix).toContain('CORI Alpha is the first independently verifiable constitutional proof');
    expect(matrix).toContain('constitutional receipt');
    expect(matrix).toContain('replay, receipt, and conformance coverage');
    expect(hierarchyDoc).toContain('The proof package SHALL include the constitutional receipt');
    expect(hierarchyDoc).toContain('replay artifact or replay path');
    expect(hierarchyDoc).toContain('conformance result');
  });
});
