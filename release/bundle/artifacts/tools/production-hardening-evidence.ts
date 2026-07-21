import { createHash } from 'node:crypto';
import { existsSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import path from 'node:path';
import { buildExternalIntegrationEvidence, type ExternalIntegrationEvidenceIndex } from './external-integration-evidence.js';

interface SurfaceDefinition {
  id: string;
  packageName: string;
  packageDir: string;
  docsPage: string;
  registryId: string;
  externalIntegration: string;
}

interface EvidenceFile {
  path: string;
  sha256: string;
  bytes: number;
}

interface SurfacePacket {
  id: string;
  packageName: string;
  status: 'release-evidence-ready' | 'blocked';
  packageDir: string;
  docsPage: string;
  registryId: string;
  checks: Record<string, boolean>;
  commands: {
    build: string;
    test: string;
  };
  replayAuditPacket: {
    replayReference: string;
    auditReference: string;
    documentationReference: string;
    requiredArtifacts: string[];
  };
  releasePackagingPacket: {
    manifestId: string;
    checksumAlgorithm: 'sha256';
    includedFiles: EvidenceFile[];
  };
  externalIntegrationPacket: {
    target: string;
    readiness: 'live-integration-verified' | 'adapter-contract-ready' | 'blocked';
    evidence: string[];
    serviceEvidenceIds: string[];
  };
  blockers: string[];
}

interface ProductionHardeningIndex {
  generatedAt: string;
  workspace: string;
  status: 'release-evidence-ready' | 'blocked';
  surfaces: SurfacePacket[];
  aggregateHash: string;
}

const root = process.cwd();
const outputDir = path.join(root, 'docs', 'release', 'production-hardening');

const surfaces: SurfaceDefinition[] = [
  {
    id: 'ul-runtime',
    packageName: '@aaes-os/ul-runtime',
    packageDir: 'packages/ul-runtime',
    docsPage: 'docs-site/docs/runtime/ul-runtime.md',
    registryId: 'UL',
    externalIntegration: 'UL cockpit verb-command adapter',
  },
  {
    id: 'csl-runtime',
    packageName: '@aaes-os/csl-runtime',
    packageDir: 'packages/csl-runtime',
    docsPage: 'docs-site/docs/runtime/csl-runtime.md',
    registryId: 'CSL',
    externalIntegration: 'constitutional artifact schema adapter',
  },
  {
    id: 'isl-runtime',
    packageName: '@aaes-os/isl-runtime',
    packageDir: 'packages/isl-runtime',
    docsPage: 'docs-site/docs/runtime/isl-runtime.md',
    registryId: 'ISL',
    externalIntegration: 'governed intent submission adapter',
  },
  {
    id: 'cic-runtime',
    packageName: '@aaes-os/cic-runtime',
    packageDir: 'packages/cic-runtime',
    docsPage: 'docs-site/docs/runtime/cic-runtime.md',
    registryId: 'CIC',
    externalIntegration: 'semantic graph inference adapter',
  },
  {
    id: 'ccc-runtime',
    packageName: '@aaes-os/ccc-runtime',
    packageDir: 'packages/ccc-runtime',
    docsPage: 'docs-site/docs/runtime/ccc-runtime.md',
    registryId: 'CCC',
    externalIntegration: 'replay ledger continuity adapter',
  },
  {
    id: 'coe-runtime',
    packageName: '@aaes-os/coe-runtime',
    packageDir: 'packages/coe-runtime',
    docsPage: 'docs-site/docs/runtime/coe-runtime.md',
    registryId: 'COE',
    externalIntegration: 'execution receipt adapter',
  },
  {
    id: 'cml-voss-runtime',
    packageName: '@aaes-os/cml-voss-runtime',
    packageDir: 'packages/cml-voss-runtime',
    docsPage: 'docs-site/docs/runtime/cml-voss-runtime.md',
    registryId: 'The Voss Binding',
    externalIntegration: 'CML/CVM corpus binding adapter',
  },
  {
    id: 'ugr-runtime',
    packageName: '@aaes-os/ugr-runtime',
    packageDir: 'packages/ugr-runtime',
    docsPage: 'docs-site/docs/runtime/ugr-runtime.md',
    registryId: 'UGR',
    externalIntegration: 'UGR knowledge/replay import adapter',
  },
  {
    id: 'gcre-sysmin',
    packageName: '@aaes-os/gcre-sysmin',
    packageDir: 'packages/gcre-sysmin',
    docsPage: 'docs-site/docs/runtime/gcre-sysmin.md',
    registryId: 'GCRE-SYSMIN-001',
    externalIntegration: 'GCRE language-family adapter',
  },
  {
    id: 'coda-runtime',
    packageName: '@aaes-os/coda-runtime',
    packageDir: 'packages/coda-runtime',
    docsPage: 'docs-site/docs/runtime/coda-runtime.md',
    registryId: 'CodaRuntime',
    externalIntegration: 'NovaCoda substrate adapter',
  },
  {
    id: 'nova-coda',
    packageName: '@aaes-os/nova-coda',
    packageDir: 'packages/nova-coda',
    docsPage: 'docs-site/docs/runtime/nova-coda.md',
    registryId: 'NovaCoda',
    externalIntegration: 'Nova substrate socket adapter',
  },
];

async function main(): Promise<void> {
  mkdirSync(outputDir, { recursive: true });

  const externalEvidence = await buildExternalIntegrationEvidence({ root, write: true });
  if (externalEvidence.status !== 'verified') {
    throw new Error(`external integration evidence blocked for: ${externalEvidence.observations.filter((observation) => observation.status === 'blocked').map((observation) => observation.id).join(', ')}`);
  }
  const packets = surfaces.map((surface) => buildSurfacePacket(surface, externalEvidence));
  const aggregateHash = hashJson(packets.map((packet) => ({ id: packet.id, status: packet.status, files: packet.releasePackagingPacket.includedFiles })));
  const index: ProductionHardeningIndex = {
    generatedAt: new Date().toISOString(),
    workspace: 'E:/project-infi',
    status: packets.every((packet) => packet.status === 'release-evidence-ready') ? 'release-evidence-ready' : 'blocked',
    surfaces: packets,
    aggregateHash,
  };

  writeJson('production-hardening-index.json', index);
  for (const packet of packets) {
    writeJson(`${packet.id}.evidence.json`, packet);
  }
  writeMarkdownIndex(index);

  const blocked = packets.filter((packet) => packet.status === 'blocked');
  if (blocked.length > 0) {
    throw new Error(`production hardening evidence blocked for: ${blocked.map((packet) => packet.id).join(', ')}`);
  }

  console.log(`production hardening evidence generated: ${packets.length} surfaces`);
  console.log(`aggregate hash: ${aggregateHash}`);
}

function buildSurfacePacket(surface: SurfaceDefinition, externalEvidence: ExternalIntegrationEvidenceIndex): SurfacePacket {
  const packageJsonPath = path.join(surface.packageDir, 'package.json');
  const srcPath = path.join(surface.packageDir, 'src', 'index.ts');
  const testPath = path.join(surface.packageDir, 'src', 'index.test.ts');
  const distPath = path.join(surface.packageDir, 'dist', 'index.js');
  const registryPath = 'packages/ulx-governance/src/ULXLanguageRegistry.ts';
  const docsPath = surface.docsPage;
  const packageJson = readJsonFile(packageJsonPath);

  const checks = {
    packageJson: existsSync(abs(packageJsonPath)),
    source: existsSync(abs(srcPath)),
    tests: existsSync(abs(testPath)),
    buildOutput: existsSync(abs(distPath)),
    docsPage: existsSync(abs(docsPath)),
    registryLive: registryContainsLiveEntry(registryPath, surface.registryId),
    packageName: packageJson?.name === surface.packageName,
    buildScript: Boolean(packageJson?.scripts?.build),
    testScript: Boolean(packageJson?.scripts?.test),
  };
  const blockers = Object.entries(checks)
    .filter(([, passed]) => !passed)
    .map(([check]) => check);
  const files = [packageJsonPath, srcPath, testPath, distPath, docsPath, registryPath]
    .filter((filePath) => existsSync(abs(filePath)))
    .map(checksumFile);

  return {
    id: surface.id,
    packageName: surface.packageName,
    status: blockers.length === 0 ? 'release-evidence-ready' : 'blocked',
    packageDir: surface.packageDir,
    docsPage: surface.docsPage,
    registryId: surface.registryId,
    checks,
    commands: {
      build: `corepack pnpm --filter ${surface.packageName} build`,
      test: `corepack pnpm --filter ${surface.packageName} test`,
    },
    replayAuditPacket: {
      replayReference: `${surface.id}.evidence.json#replayAuditPacket`,
      auditReference: `${surface.id}.evidence.json#checks`,
      documentationReference: surface.docsPage,
      requiredArtifacts: ['packageJson', 'source', 'tests', 'buildOutput', 'docsPage', 'registryLive'],
    },
    releasePackagingPacket: {
      manifestId: `${surface.id}-${hashJson(files.map((file) => [file.path, file.sha256]))}`,
      checksumAlgorithm: 'sha256',
      includedFiles: files,
    },
    externalIntegrationPacket: {
      target: surface.externalIntegration,
      readiness: blockers.length === 0 ? 'live-integration-verified' : 'blocked',
      evidence: [
        surface.docsPage,
        `${surface.packageDir}/src/index.ts`,
        `${surface.id}.evidence.json`,
        'docs/release/external-integrations/README.md',
        'docs/release/external-integrations/external-integration-index.json',
      ],
      serviceEvidenceIds: externalEvidence.observations.map((observation) => observation.id),
    },
    blockers,
  };
}

function registryContainsLiveEntry(registryPath: string, registryId: string): boolean {
  const text = readFileSync(abs(registryPath), 'utf8');
  const idIndex = text.indexOf(`id: '${registryId}'`);
  if (idIndex < 0) {
    return false;
  }
  const nextEntryIndex = text.indexOf('\n  {', idIndex + 1);
  const entry = nextEntryIndex < 0 ? text.slice(idIndex) : text.slice(idIndex, nextEntryIndex);
  return entry.includes("status: 'live'");
}

function writeMarkdownIndex(index: ProductionHardeningIndex): void {
  const lines = [
    '# Production Hardening Evidence',
    '',
    `Generated: ${index.generatedAt}`,
    '',
    `Aggregate hash: \`${index.aggregateHash}\``,
    '',
    `Status: \`${index.status}\``,
    '',
    '| Surface | Status | Replay/audit | Release package | External integration |',
    '| --- | --- | --- | --- | --- |',
    ...index.surfaces.map((surface) => {
      return `| ${surface.packageName} | ${surface.status} | ${surface.replayAuditPacket.replayReference} | ${surface.releasePackagingPacket.manifestId} | ${surface.externalIntegrationPacket.readiness} |`;
    }),
    '',
    'This generated index is evidence, not a production publication by itself. It records the replay/audit, release-packaging, and external-integration readiness packets for promoted live runtime surfaces.',
    '',
  ];

  writeFileSync(path.join(outputDir, 'README.md'), `${lines.join('\n')}\n`, 'utf8');
}

function checksumFile(filePath: string): EvidenceFile {
  const buffer = readFileSync(abs(filePath));
  return {
    path: normalizePath(filePath),
    sha256: createHash('sha256').update(buffer).digest('hex'),
    bytes: buffer.length,
  };
}

function readJsonFile(filePath: string): { name?: string; scripts?: Record<string, string> } | undefined {
  if (!existsSync(abs(filePath))) {
    return undefined;
  }
  return JSON.parse(readFileSync(abs(filePath), 'utf8')) as { name?: string; scripts?: Record<string, string> };
}

function writeJson(fileName: string, value: unknown): void {
  writeFileSync(path.join(outputDir, fileName), `${JSON.stringify(value, null, 2)}\n`, 'utf8');
}

function hashJson(value: unknown): string {
  return createHash('sha256').update(JSON.stringify(stableValue(value))).digest('hex');
}

function stableValue(value: unknown): unknown {
  if (Array.isArray(value)) {
    return value.map(stableValue);
  }
  if (value && typeof value === 'object') {
    return Object.fromEntries(
      Object.entries(value as Record<string, unknown>)
        .sort(([left], [right]) => left.localeCompare(right))
        .map(([key, entry]) => [key, stableValue(entry)]),
    );
  }
  return value;
}

function abs(filePath: string): string {
  return path.join(root, filePath);
}

function normalizePath(filePath: string): string {
  return filePath.replace(/\\/g, '/');
}

main().catch((error: unknown) => {
  console.error(error instanceof Error ? error.message : String(error));
  process.exitCode = 1;
});
