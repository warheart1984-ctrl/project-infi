import { describe, expect, it } from 'vitest';

import {
  createDemoProofSurfaceRegistry,
  createConstitutionalEvidenceGraphFromProofSurfaces,
  resolveConstitutionalEvidenceGraphFromProofSurfaces,
  summarizeConstitutionalEvidenceGraph,
  validateConstitutionalEvidenceGraph,
} from './index.js';
import { createReleaseReceipt, validateReleaseReceipt } from '../../../release/receipt.ts';

describe('Constitutional evidence graph', () => {
  it('resolves the release evidence graph from proof surfaces', () => {
    const surfaces = createDemoProofSurfaceRegistry().list();
    const graph = resolveConstitutionalEvidenceGraphFromProofSurfaces(surfaces, {
      source: 'local-registry',
    });

    expect(graph.rootReceipt.receiptId).toBe('graph:local-registry');
    expect(graph.summary.rootReceiptId).toBe('graph:local-registry');
    expect(graph.summary.proofSurfaceCount).toBeGreaterThan(0);
    expect(graph.summary.claimCount).toBeGreaterThan(0);
    expect(graph.unresolvedClaims).toHaveLength(0);
    expect(validateConstitutionalEvidenceGraph(graph).some((issue) => issue.severity === 'error')).toBe(false);
  });

  it('summarizes graph-backed evidence without losing the root receipt', () => {
    const surfaces = createDemoProofSurfaceRegistry().list();
    const graph = createConstitutionalEvidenceGraphFromProofSurfaces(surfaces);
    const summary = summarizeConstitutionalEvidenceGraph(graph);

    expect(summary.rootReceiptId).toBe(graph.rootReceipt.receiptId);
    expect(summary.viewCount).toBeGreaterThan(0);
    expect(summary.verifiedClaimCount).toBeGreaterThan(0);
  });

  it('keeps the release receipt as the graph root without recursive embedding', () => {
    const receipt = createReleaseReceipt(
      {
        name: 'aaes-os',
        version: '0.1.0',
        bundle: 'release/bundle',
        artifacts: ['release/receipt.ts'],
      },
      {
        files: ['release/checksums.json'],
      },
      {
        generatedAt: '2026-07-08T00:00:00.000Z',
      },
    );

    expect(receipt.constitutionalEvidenceGraph?.rootReceipt.receiptId).toBe(receipt.receiptId);
    expect(receipt.constitutionalEvidenceGraph?.rootReceipt.constitutionalEvidenceGraph).toBeUndefined();
    expect(() => JSON.stringify(receipt)).not.toThrow();
    expect(validateReleaseReceipt(receipt)).toHaveLength(0);
  });

  it('rejects public claims that are not backed by a verifiable proof surface', () => {
    const surfaces = createDemoProofSurfaceRegistry().list();
    const graph = createConstitutionalEvidenceGraphFromProofSurfaces(surfaces);
    const tamperedGraph = structuredClone(graph);
    const proofSurfaceNode = tamperedGraph.nodes.find((node) => node.kind === 'proof-surface');

    expect(proofSurfaceNode).toBeDefined();
    if (!proofSurfaceNode) {
      return;
    }

    proofSurfaceNode.verified = false;

    const issues = validateConstitutionalEvidenceGraph(tamperedGraph);
    expect(issues.some((issue) => issue.message.includes('verifiable proof surface'))).toBe(true);
  });
});
