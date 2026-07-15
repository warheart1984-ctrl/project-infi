#!/usr/bin/env node
import { readFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

export interface ExternalStandardsFamily {
  family: string;
  exampleStandards: string[];
  cisFocus: string[];
}

export interface ExternalStandardsMapping {
  family: string;
  supports: string[];
  rationale: string;
}

export interface ExternalStandardsSpec {
  specId: string;
  displayName: string;
  version: string;
  status: string;
  standardsFamilies: ExternalStandardsFamily[];
  mappings: ExternalStandardsMapping[];
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

function isExternalStandardsSpec(value: unknown): value is ExternalStandardsSpec {
  if (typeof value !== 'object' || value === null) {
    return false;
  }
  const spec = value as Partial<ExternalStandardsSpec>;
  return (
    isString(spec.specId) &&
    isString(spec.displayName) &&
    isString(spec.version) &&
    isString(spec.status) &&
    Array.isArray(spec.standardsFamilies) &&
    Array.isArray(spec.mappings) &&
    spec.standardsFamilies.every((family) => typeof family === 'object' && family !== null && isString((family as ExternalStandardsFamily).family) && isStringArray((family as ExternalStandardsFamily).exampleStandards) && isStringArray((family as ExternalStandardsFamily).cisFocus)) &&
    spec.mappings.every((mapping) => typeof mapping === 'object' && mapping !== null && isString((mapping as ExternalStandardsMapping).family) && isStringArray((mapping as ExternalStandardsMapping).supports) && isString((mapping as ExternalStandardsMapping).rationale))
  );
}

export function loadExternalStandardsSpec(): ExternalStandardsSpec {
  const raw = JSON.parse(readFileSync(releasePath('EXTERNAL_STANDARDS_MAPPING.spec.json'), 'utf8')) as unknown;
  if (!isExternalStandardsSpec(raw)) {
    throw new Error('EXTERNAL_STANDARDS_MAPPING.spec.json is malformed');
  }
  return raw;
}

export function summarizeExternalStandardsSpec(spec = loadExternalStandardsSpec()): {
  familyCount: number;
  mappingCount: number;
} {
  return {
    familyCount: spec.standardsFamilies.length,
    mappingCount: spec.mappings.length,
  };
}
