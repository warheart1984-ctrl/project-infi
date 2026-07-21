import { describe, expect, it } from 'vitest';
import {
  deriveCisCompanionSpecRegistry,
  deriveCisConformanceSuiteInput,
  loadCisStandardsBundle,
  loadCisStandardsHierarchySpec,
} from '../../tools/cis-standards.js';

describe('cis standards importer', () => {
  it('loads the hierarchy spec and derives a conformance input from it', () => {
    const hierarchy = loadCisStandardsHierarchySpec();
    const conformanceInput = deriveCisConformanceSuiteInput(hierarchy);

    expect(hierarchy.specId).toBe('cis-standards-hierarchy');
    expect(hierarchy.cisCorePrinciples.some((principle) => principle.id === 'cis-principle-longevity')).toBe(true);
    expect(conformanceInput.generatedFrom).toBe('cis-standards-hierarchy');
    expect(conformanceInput.requirements.length).toBe(hierarchy.traceabilityMatrix.length);
    expect(conformanceInput.requirements[0]?.tests.length).toBeGreaterThan(0);
  });

  it('derives a companion registry that includes core, companions, profiles, and Research OS', () => {
    const hierarchy = loadCisStandardsHierarchySpec();
    const registry = deriveCisCompanionSpecRegistry(hierarchy);

    expect(registry.core.name).toBe('CIS Core');
    expect(registry.companionSpecifications.some((spec) => spec.name === 'Reference Architecture')).toBe(true);
    expect(registry.implementationProfiles).toContain('Research');
    expect(registry.researchOS.flow).toEqual(['Evidence', 'Insights', 'Ideas', 'Actions']);
  });

  it('loads the full standards bundle for orchestrator ingestion', () => {
    const bundle = loadCisStandardsBundle();

    expect(bundle.hierarchy.governanceProcess.partOfSpecSurface).toBe(true);
    expect(bundle.conformanceInput.requirements.some((entry) => entry.id === 'CR-4')).toBe(true);
    expect(bundle.companionRegistry.specId).toBe('cis-companion-spec-registry');
  });
});
