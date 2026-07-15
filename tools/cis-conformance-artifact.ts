#!/usr/bin/env node
import { mkdirSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { writeGeneratedCisConformanceSuiteInput } from './cis-conformance.js';

function repoRoot(): string {
  return path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
}

function main(): void {
  const outputPath = path.join(repoRoot(), 'ci-artifacts', 'generated', 'CIS_CONFORMANCE_SUITE_INPUT.spec.json');
  mkdirSync(path.dirname(outputPath), { recursive: true });
  const writtenPath = writeGeneratedCisConformanceSuiteInput(outputPath);
  process.stdout.write(`${writtenPath}\n`);
}

main();
