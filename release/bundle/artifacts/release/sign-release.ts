import {
  computeSignature,
  getBundleChecksumsPath,
  getBundleManifestPath,
  getBundleSignaturePath,
  getChecksumsPath,
  getSignaturePath,
  loadManifest,
  readJson,
  writeJson,
} from './shared.ts';
import { attachReleaseSignature, readReleaseReceipt, syncReleaseReceipt, validateReleaseReceipt } from './receipt.ts';

function main() {
  const manifest = loadManifest();
  const checksums = readJson(getChecksumsPath(), null);
  if (!checksums || !Array.isArray(checksums.files)) {
    throw new Error('release checksums are missing; run build-release first');
  }

  const signature = computeSignature(checksums.files, manifest);
  const payload = {
    signature,
    artifactCount: checksums.files.length,
    generatedAt: new Date().toISOString(),
  };

  writeJson(getSignaturePath(), payload);
  writeJson(getBundleSignaturePath(), payload);
  writeJson(getBundleChecksumsPath(), {
    ...checksums,
    signature,
  });

  // Keep the bundle manifest in sync with the signed package state.
  const bundleManifest = readJson(getBundleManifestPath(), {});
  writeJson(getBundleManifestPath(), {
    ...bundleManifest,
    signature,
  });

  const receipt = readReleaseReceipt();
  if (!receipt) {
    throw new Error('release receipt is missing; run build-release first');
  }
  const receiptIssues = validateReleaseReceipt(receipt);
  if (receiptIssues.length > 0) {
    throw new Error(`release receipt is invalid: ${receiptIssues.join('; ')}`);
  }
  syncReleaseReceipt(attachReleaseSignature(receipt, signature));

  console.log(`release signed: ${signature}`);
}

main();
