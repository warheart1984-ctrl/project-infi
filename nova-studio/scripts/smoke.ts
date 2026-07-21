import { readdir, readFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

import {
  verifyReplayCoverage,
} from '@aaes-os/aaes-governance';

import { LOCAL_PROOF_SURFACE_CATALOG_URL } from '../src/catalogConfig.js';
import { loadNovaStudioProofSurfaces } from '../src/proofSurfaces.js';

const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const studioRoot = path.resolve(scriptDir, '..');
const distRoot = path.join(studioRoot, 'dist');

async function assertDistExists(): Promise<void> {
  const indexPath = path.join(distRoot, 'index.html');
  const indexHtml = await readFile(indexPath, 'utf8');
  if (!indexHtml.includes('<div id="root">')) {
    throw new Error('Nova Studio smoke failed: index.html does not include the application root');
  }

  const entries = await readdir(path.join(distRoot, 'assets'));
  if (!entries.some((entry) => entry.endsWith('.js'))) {
    throw new Error('Nova Studio smoke failed: no JavaScript bundle found in dist/assets/');
  }
}

function assertSurfaceIdentity(surfaces: readonly { identity: { id: string } }[]): void {
  if (!surfaces.some((surface) => surface.identity.id === '@aaes-os/nova-studio')) {
    throw new Error('Nova Studio smoke failed: local registry is missing the Nova Studio proof surface');
  }
  if (!surfaces.some((surface) => surface.identity.id === '@aaes-os/sovereignx-router')) {
    throw new Error('Nova Studio smoke failed: local registry is missing the SovereignX Router proof surface');
  }
}

async function main(): Promise<void> {
  await assertDistExists();

  const catalog = await loadNovaStudioProofSurfaces(LOCAL_PROOF_SURFACE_CATALOG_URL);
  const replayReport = verifyReplayCoverage(catalog.replayableSurfaces);

  assertSurfaceIdentity(catalog.replayableSurfaces);

  if (catalog.source !== 'local-registry') {
    throw new Error(`Nova Studio smoke failed: expected local-registry source, received ${catalog.source}`);
  }
  if (!replayReport.passed) {
    const messages = replayReport.issues.map((issue) => `${issue.field}: ${issue.message}`).join('; ');
    throw new Error(`Nova Studio smoke failed: replay coverage validation failed (${messages})`);
  }

  console.log(
    `Nova Studio smoke passed: ${catalog.surfaces.length} surfaces, ${replayReport.replayableSurfaces} replayable, dist=${distRoot}`,
  );
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
