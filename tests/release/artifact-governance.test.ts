import { describe, expect, it } from 'vitest';
import { loadArtifactGovernanceRegistry, summarizeArtifactGovernanceRegistry } from '../../tools/artifact-governance.js';

describe('artifact governance registry', () => {
  it('loads the registry and exposes the shared governance fields', () => {
    const registry = loadArtifactGovernanceRegistry();

    expect(registry.governanceModel.requiredFields).toEqual([
      'Document Status',
      'Version',
      'Owner / Steward',
      'Normative or Informative',
      'Parent Specification',
      'Traceability Links',
      'CCP / CCR History',
      'Release History',
    ]);
    expect(registry.artifacts.some((artifact) => artifact.artifactId === 'cis-standards-hierarchy')).toBe(true);
    expect(registry.artifacts.some((artifact) => artifact.classification === 'Normative')).toBe(true);
    expect(registry.artifacts.map((artifact) => artifact.artifactId)).toEqual(
      expect.arrayContaining([
        'reference-architecture',
        'ontology',
        'knowledge-graph-specification',
        'conformance-suite',
        'reference-runtime',
        'standards-traceability-matrix',
        'implementation-profiles',
        'dx-guide',
        'documentation-specification-family',
        'external-standards-mapping',
        'cis-conformance-suite-input',
        'cis-conformance-suite-generation',
        'profile-government',
        'profile-healthcare',
        'profile-finance',
        'profile-research',
        'profile-education',
        'profile-infrastructure',
        'profile-regenerative-intelligence',
      ]),
    );
  });

  it('summarizes the registry for orchestrator ingestion', () => {
    const summary = summarizeArtifactGovernanceRegistry();

    expect(summary.specId).toBe('artifact-governance-registry');
    expect(summary.artifactCount).toBeGreaterThan(0);
    expect(summary.normativeCount).toBeGreaterThan(0);
    expect(summary.informativeCount).toBeGreaterThan(0);
  });
});
