import { describe, expect, it } from 'vitest';
import { readFileSync } from 'node:fs';
import path from 'node:path';

describe('recent document subsystem coverage', () => {
  it('maps all 38 recent documents to AAES OS subsystem coverage', () => {
    const coveragePath = path.resolve('docs/coverage/recent-doc-subsystem-coverage.json');
    const coverage = JSON.parse(readFileSync(coveragePath, 'utf8')) as {
      inventory: { expectedCount: number };
      documents: { path: string; subsystem: string; coverageType: string; codeRefs: string[]; testRefs: string[] }[];
    };

    expect(coverage.inventory.expectedCount).toBe(38);
    expect(coverage.documents).toHaveLength(38);
    for (const doc of coverage.documents) {
      expect(doc.path).toBeTruthy();
      expect(doc.subsystem).toBeTruthy();
      expect(['implemented', 'imported-contract', 'reference-only', 'tested-bridge']).toContain(doc.coverageType);
      expect(doc.codeRefs.length + doc.testRefs.length).toBeGreaterThan(0);
    }
  });
});
