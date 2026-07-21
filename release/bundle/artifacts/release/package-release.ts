import { dirname, join, resolve } from 'node:path';

import {
  copyArtifactTree,
  ensureDir,
  getBundleChecksumsPath,
  getBundleManifestPath,
  getBundleRoot,
  getChecksumsPath,
  getManifestPath,
  getReceiptPath,
  loadManifest,
  readJson,
  writeJson,
} from './shared.ts';

function main() {
  const manifest = loadManifest();
  const checksums = readJson(getChecksumsPath(), null);
  if (!checksums || !Array.isArray(checksums.files)) {
    throw new Error('release checksums are missing; run build-release first');
  }

  ensureDir(getBundleRoot());
  const packageFiles = [];
  for (const artifact of manifest.artifacts) {
    const sourcePath = resolve(dirname(getManifestPath()), '..', artifact);
    const bundledPath = copyArtifactTree(sourcePath, getBundleRoot(), join('artifacts', artifact));
    packageFiles.push({
      path: artifact,
      bundledPath,
    });
  }

  copyArtifactTree(getReceiptPath(), getBundleRoot(), 'constitutional-release-receipt.json');

  writeJson(getBundleManifestPath(), {
    name: manifest.name,
    version: manifest.version,
    bundle: manifest.bundle,
    artifactCount: packageFiles.length,
    artifacts: packageFiles.map((entry) => entry.path),
    generatedAt: new Date().toISOString(),
  });
  writeJson(getBundleChecksumsPath(), checksums);

  console.log(`release package built: ${packageFiles.length} artifacts`);
}

main();
