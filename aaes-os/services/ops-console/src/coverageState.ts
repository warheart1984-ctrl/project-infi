import { existsSync, readFileSync } from 'node:fs';
import path from 'node:path';

export interface SubsystemCoverageRecord {
  path: string;
  subsystem: string;
  coverageType: 'implemented' | 'imported-contract' | 'reference-only' | 'tested-bridge';
  codeRefs: string[];
  testRefs: string[];
}

export interface SubsystemCoverageManifest {
  inventory: {
    generatedAt: string;
    windowDays: number;
    expectedCount: number;
    scope: string;
  };
  documents: SubsystemCoverageRecord[];
}

export function getSubsystemCoverage(): SubsystemCoverageManifest {
  const manifestPath = findCoverageManifest();
  return JSON.parse(readFileSync(manifestPath, 'utf8')) as SubsystemCoverageManifest;
}

function findCoverageManifest(): string {
  const relative = path.join('docs', 'coverage', 'recent-doc-subsystem-coverage.json');
  let current = process.cwd();
  for (let index = 0; index < 6; index += 1) {
    const candidate = path.join(current, relative);
    if (existsSync(candidate)) {
      return candidate;
    }
    const parent = path.dirname(current);
    if (parent === current) {
      break;
    }
    current = parent;
  }
  return path.resolve(relative);
}
