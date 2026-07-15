#!/usr/bin/env node
import { readFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

export interface CisHierarchyPrinciple {
  id: string;
  name: string;
  statement: string;
}

export interface CisHierarchyRequirement {
  id: string;
  name: string;
  statement: string;
  verification: string;
}

export interface CisTraceabilityRow {
  requirement: string;
  component: string;
  evidence: string[];
  test: string;
}

export interface CisStandardsHierarchySpec {
  specId: string;
  displayName: string;
  version: string;
  status: string;
  cisCorePrinciples: CisHierarchyPrinciple[];
  conformanceCriteria: CisHierarchyRequirement[];
  coreSpecification: {
    name: string;
    role: string;
    inheritanceRule: string;
  };
  governanceModel: {
    documentStatusLifecycle: string[];
    governanceFields: string[];
  };
  companionSpecifications: Array<{
    name: string;
    responsibility: string;
  }>;
  implementationProfiles: string[];
  researchOS: {
    name: string;
    role: string;
    flow: string[];
  };
  governanceProcess: {
    partOfSpecSurface: boolean;
    documentStatusLifecycle: string[];
    requiredArtifacts: string[];
  };
  traceabilityMatrix: CisTraceabilityRow[];
}

export interface CisConformanceSuiteCase {
  id: string;
  requirement: string;
  component: string;
  evidence: string[];
  tests: string[];
}

export interface CisConformanceValidationFamily {
  id: string;
  name: string;
  purpose: string;
  acceptanceCriteria: string[];
}

export interface CisConformanceSuiteInput {
  specId: string;
  displayName: string;
  version: string;
  status: string;
  generatedFrom: string;
  traceabilityPath: string[];
  requirements: CisConformanceSuiteCase[];
  validationFamilies: CisConformanceValidationFamily[];
  acceptanceCriteria: string[];
}

export interface CisCompanionSpecRegistry {
  specId: string;
  displayName: string;
  version: string;
  generatedFrom: string;
  core: {
    name: string;
    role: string;
  };
  companionSpecifications: Array<{
    name: string;
    responsibility: string;
  }>;
  implementationProfiles: string[];
  researchOS: {
    name: string;
    role: string;
    flow: string[];
  };
}

export interface CisStandardsBundle {
  hierarchy: CisStandardsHierarchySpec;
  conformanceInput: CisConformanceSuiteInput;
  companionRegistry: CisCompanionSpecRegistry;
}

function repoRoot(): string {
  return path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
}

function releasePath(fileName: string): string {
  return path.join(repoRoot(), 'docs', 'crk1', 'release', fileName);
}

function readJsonFile<T>(fileName: string): T {
  return JSON.parse(readFileSync(releasePath(fileName), 'utf8')) as T;
}

function isString(value: unknown): value is string {
  return typeof value === 'string' && value.trim().length > 0;
}

function isStringArray(value: unknown): value is string[] {
  return Array.isArray(value) && value.every(isString);
}

function isTraceabilityRow(value: unknown): value is CisTraceabilityRow {
  if (typeof value !== 'object' || value === null) {
    return false;
  }
  const row = value as Partial<CisTraceabilityRow>;
  return isString(row.requirement) && isString(row.component) && isString(row.test) && isStringArray(row.evidence);
}

function isHierarchySpec(value: unknown): value is CisStandardsHierarchySpec {
  if (typeof value !== 'object' || value === null) {
    return false;
  }
  const spec = value as Partial<CisStandardsHierarchySpec>;
  return (
    isString(spec.specId) &&
    isString(spec.displayName) &&
    isString(spec.version) &&
    isString(spec.status) &&
    Array.isArray(spec.cisCorePrinciples) &&
    Array.isArray(spec.conformanceCriteria) &&
    Array.isArray(spec.companionSpecifications) &&
    isStringArray(spec.implementationProfiles) &&
    isTraceabilityRows(spec.traceabilityMatrix) &&
    typeof spec.coreSpecification === 'object' &&
    spec.coreSpecification !== null &&
    typeof spec.governanceModel === 'object' &&
    spec.governanceModel !== null &&
    typeof spec.researchOS === 'object' &&
    spec.researchOS !== null &&
    typeof spec.governanceProcess === 'object' &&
    spec.governanceProcess !== null
  );
}

function isTraceabilityRows(value: unknown): value is CisTraceabilityRow[] {
  return Array.isArray(value) && value.every(isTraceabilityRow);
}

export function loadCisStandardsHierarchySpec(): CisStandardsHierarchySpec {
  const hierarchy = readJsonFile<unknown>('CIS_STANDARDS_HIERARCHY.spec.json');
  if (!isHierarchySpec(hierarchy)) {
    throw new Error('CIS_STANDARDS_HIERARCHY.spec.json is malformed');
  }
  return hierarchy;
}

export function deriveCisConformanceSuiteInput(hierarchy: CisStandardsHierarchySpec): CisConformanceSuiteInput {
  return {
    specId: 'cis-conformance-suite-input',
    displayName: 'CIS Conformance Suite Input',
    version: hierarchy.version,
    status: hierarchy.status,
    generatedFrom: hierarchy.specId,
    traceabilityPath: [
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
    ],
    requirements: hierarchy.traceabilityMatrix.map((row, index) => ({
      id: `CR-${index + 1}`,
      requirement: row.requirement,
      component: row.component,
      evidence: [...row.evidence],
      tests: [row.test],
    })),
    validationFamilies: [
      {
        id: 'VF-1',
        name: 'Constitutional Verification',
        purpose: 'Verify that each requirement traces through the full constitutional path.',
        acceptanceCriteria: [
          'Every requirement maps to Architecture, Ontology, Knowledge Graph, GKS, Research OS, Reference Runtime, Conformance, Evidence, Replay, and External Standards.',
          'Every requirement has a stable component and evidence surface.',
          'No requirement invents a new constitutional obligation.',
        ],
      },
      {
        id: 'VF-2',
        name: 'Replay Validation',
        purpose: 'Verify that the evidence package can be reconstructed deterministically from the recorded replay path.',
        acceptanceCriteria: [
          'Replay produces the recorded evidence package.',
          'Replay does not depend on private explanation or hidden state.',
          'Replay confirms the governing decision record.',
        ],
      },
      {
        id: 'VF-3',
        name: 'Receipt Validation',
        purpose: 'Verify that the constitutional receipt set is complete and consistent with the governing record.',
        acceptanceCriteria: [
          'Required receipts are present.',
          'Each receipt matches the governing decision record.',
          'No receipt contradicts the evidence package.',
        ],
      },
      {
        id: 'VF-4',
        name: 'Trust Validation',
        purpose: 'Verify canonical state, stewardship, and trust ledger consistency.',
        acceptanceCriteria: [
          'Canonical state is internally consistent.',
          'Stewardship records are traceable.',
          'Trust ledger entries agree with canonical transitions.',
        ],
      },
      {
        id: 'VF-5',
        name: 'Acceptance Criteria',
        purpose: 'Verify that the suite records an objective pass, partial, or fail outcome.',
        acceptanceCriteria: [
          'No blocking requirement remains unverified for pass.',
          'Partial states are recorded explicitly.',
          'Subjective readiness claims do not override evidence.',
        ],
      },
    ],
    acceptanceCriteria: [
      'The suite remains synchronized with the traceability matrix.',
      'The suite input remains machine-readable and replayable.',
      'The suite produces evidence-first outcomes only.',
      'The suite identifies blocking gaps instead of overstating readiness.',
    ],
  };
}

export function deriveCisCompanionSpecRegistry(hierarchy: CisStandardsHierarchySpec): CisCompanionSpecRegistry {
  return {
    specId: 'cis-companion-spec-registry',
    displayName: 'CIS Companion Specification Registry',
    version: hierarchy.version,
    generatedFrom: hierarchy.specId,
    core: {
      name: hierarchy.coreSpecification.name,
      role: hierarchy.coreSpecification.role,
    },
    companionSpecifications: hierarchy.companionSpecifications.map((spec) => ({ ...spec })),
    implementationProfiles: [...hierarchy.implementationProfiles],
    researchOS: {
      name: hierarchy.researchOS.name,
      role: hierarchy.researchOS.role,
      flow: [...hierarchy.researchOS.flow],
    },
  };
}

export function loadCisStandardsBundle(): CisStandardsBundle {
  const hierarchy = loadCisStandardsHierarchySpec();
  return {
    hierarchy,
    conformanceInput: deriveCisConformanceSuiteInput(hierarchy),
    companionRegistry: deriveCisCompanionSpecRegistry(hierarchy),
  };
}
