import { readFileSync } from 'node:fs';
import path from 'node:path';

interface CoverageManifest {
  inventory: { expectedCount: number };
  documents: {
    path: string;
    subsystem: string;
    coverageType: 'implemented' | 'imported-contract' | 'reference-only' | 'tested-bridge';
    codeRefs: string[];
    testRefs: string[];
  }[];
}

const manifestPath = path.resolve('docs/coverage/recent-doc-subsystem-coverage.json');
const manifest = JSON.parse(readFileSync(manifestPath, 'utf8')) as CoverageManifest;

const failures: string[] = [];

if (manifest.documents.length !== manifest.inventory.expectedCount) {
  failures.push(`expected ${manifest.inventory.expectedCount} documents, found ${manifest.documents.length}`);
}

const seen = new Set<string>();
for (const doc of manifest.documents) {
  if (!doc.path.trim()) failures.push('document path is empty');
  if (!doc.subsystem.trim()) failures.push(`${doc.path}: subsystem is empty`);
  if (seen.has(doc.path)) failures.push(`${doc.path}: duplicate document path`);
  seen.add(doc.path);
  if (!['implemented', 'imported-contract', 'reference-only', 'tested-bridge'].includes(doc.coverageType)) {
    failures.push(`${doc.path}: invalid coverageType ${doc.coverageType}`);
  }
  if (doc.codeRefs.length + doc.testRefs.length === 0) {
    failures.push(`${doc.path}: missing codeRefs/testRefs`);
  }
}

if (failures.length > 0) {
  console.error('Recent document coverage check failed:');
  for (const failure of failures) {
    console.error(`- ${failure}`);
  }
  process.exit(1);
}

console.log(`Recent document coverage check passed: ${manifest.documents.length}/${manifest.inventory.expectedCount} documents mapped.`);
