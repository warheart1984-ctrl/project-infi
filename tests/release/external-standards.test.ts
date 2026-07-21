import { describe, expect, it } from 'vitest';
import { loadExternalStandardsSpec, summarizeExternalStandardsSpec } from '../../tools/external-standards.js';

describe('external standards mapping', () => {
  it('loads the mapping layer and includes the major standards families', () => {
    const spec = loadExternalStandardsSpec();

    expect(spec.standardsFamilies.map((family) => family.family)).toEqual(
      expect.arrayContaining(['ISO', 'NIST', 'IEEE', 'W3C', 'IETF']),
    );
    expect(spec.mappings.some((mapping) => mapping.family === 'W3C')).toBe(true);
  });

  it('summarizes the mapping layer for orchestrator ingestion', () => {
    const summary = summarizeExternalStandardsSpec();

    expect(summary.familyCount).toBeGreaterThanOrEqual(5);
    expect(summary.mappingCount).toBeGreaterThanOrEqual(5);
  });
});
