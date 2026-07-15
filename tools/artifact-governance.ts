#!/usr/bin/env node
import { readFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

export interface ArtifactGovernanceChange {
  id: string;
  status: string;
  summary: string;
}

export interface ArtifactGovernanceRelease {
  version: string;
  date: string;
  note: string;
}

export interface ArtifactGovernanceEntry {
  artifactId: string;
  title: string;
  documentStatus: string;
  version: string;
  ownerSteward: string;
  classification: 'Normative' | 'Informative';
  parentSpecification: string;
  traceabilityLinks: string[];
  ccpCcrHistory: ArtifactGovernanceChange[];
  releaseHistory: ArtifactGovernanceRelease[];
}

export interface ArtifactGovernanceRegistry {
  specId: string;
  displayName: string;
  version: string;
  status: string;
  governanceModel: {
    documentStatusLifecycle: string[];
    requiredFields: string[];
  };
  artifacts: ArtifactGovernanceEntry[];
}

function repoRoot(): string {
  return path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
}

function releasePath(fileName: string): string {
  return path.join(repoRoot(), 'docs', 'crk1', 'release', fileName);
}

function isString(value: unknown): value is string {
  return typeof value === 'string' && value.trim().length > 0;
}

function isStringArray(value: unknown): value is string[] {
  return Array.isArray(value) && value.every(isString);
}

function isRegistry(value: unknown): value is ArtifactGovernanceRegistry {
  if (typeof value !== 'object' || value === null) {
    return false;
  }
  const registry = value as Partial<ArtifactGovernanceRegistry>;
  return (
    isString(registry.specId) &&
    isString(registry.displayName) &&
    isString(registry.version) &&
    isString(registry.status) &&
    typeof registry.governanceModel === 'object' &&
    registry.governanceModel !== null &&
    isStringArray(registry.governanceModel.documentStatusLifecycle) &&
    isStringArray(registry.governanceModel.requiredFields) &&
    Array.isArray(registry.artifacts)
  );
}

export function loadArtifactGovernanceRegistry(): ArtifactGovernanceRegistry {
  const raw = JSON.parse(readFileSync(releasePath('ARTIFACT_GOVERNANCE_REGISTRY.spec.json'), 'utf8')) as unknown;
  if (!isRegistry(raw)) {
    throw new Error('ARTIFACT_GOVERNANCE_REGISTRY.spec.json is malformed');
  }
  return raw;
}

export function summarizeArtifactGovernanceRegistry(registry = loadArtifactGovernanceRegistry()): {
  specId: string;
  artifactCount: number;
  normativeCount: number;
  informativeCount: number;
} {
  const normativeCount = registry.artifacts.filter((artifact) => artifact.classification === 'Normative').length;
  const informativeCount = registry.artifacts.filter((artifact) => artifact.classification === 'Informative').length;
  return {
    specId: registry.specId,
    artifactCount: registry.artifacts.length,
    normativeCount,
    informativeCount,
  };
}
