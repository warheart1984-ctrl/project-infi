import {
  getArtifactRecords,
  getChecksumsPath,
  loadManifest,
  writeJson,
} from './shared.ts';
import { createReleaseReceipt, writeReleaseReceipt } from './receipt.ts';

function main() {
  const manifest = loadManifest();
  const artifacts = getArtifactRecords(manifest);
  const checksumBundle = {
    name: manifest.name,
    version: manifest.version,
    bundle: manifest.bundle,
    files: artifacts.map((artifact) => ({
      path: artifact.path,
      sha256: artifact.sha256,
      size: artifact.size,
    })),
    signature: null,
  };

  writeJson(getChecksumsPath(), checksumBundle);
  writeReleaseReceipt(createReleaseReceipt(manifest, checksumBundle));

  console.log(`release manifest built: ${artifacts.length} artifacts`);
}

main();
