#!/usr/bin/env node
import { readFileSync, writeFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import {
  deriveCisConformanceSuiteInput,
  loadCisStandardsHierarchySpec,
  type CisConformanceSuiteInput,
} from './cis-standards.js';

function repoRoot(): string {
  return path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
}

function releasePath(fileName: string): string {
  return path.join(repoRoot(), 'docs', 'crk1', 'release', fileName);
}

export function generateCisConformanceSuiteInput(): CisConformanceSuiteInput {
  const hierarchy = loadCisStandardsHierarchySpec();
  return deriveCisConformanceSuiteInput(hierarchy);
}

export function loadCommittedCisConformanceSuiteInput(): CisConformanceSuiteInput {
  return JSON.parse(readFileSync(releasePath('CIS_CONFORMANCE_SUITE_INPUT.spec.json'), 'utf8')) as CisConformanceSuiteInput;
}

export function writeGeneratedCisConformanceSuiteInput(outputPath = releasePath('CIS_CONFORMANCE_SUITE_INPUT.spec.json')): string {
  const output = JSON.stringify(generateCisConformanceSuiteInput(), null, 2);
  writeFileSync(outputPath, `${output}\n`, 'utf8');
  return outputPath;
}
