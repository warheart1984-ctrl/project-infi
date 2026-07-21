import { createHash } from 'node:crypto';
import { copyFileSync, existsSync, mkdirSync, readFileSync, readdirSync, statSync, writeFileSync } from 'node:fs';
import { dirname, isAbsolute, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const repoRoot = resolve(dirname(fileURLToPath(import.meta.url)), '..');

function resolveReleaseRoot() {
  const override = process.env.AAES_RELEASE_DIR;
  if (!override) {
    return resolve(repoRoot, 'release');
  }
  return isAbsolute(override) ? override : resolve(repoRoot, override);
}

export function getRepoRoot() {
  return repoRoot;
}

export function getReleaseRoot() {
  return resolveReleaseRoot();
}

export function getBundleRoot() {
  return resolve(getReleaseRoot(), 'bundle');
}

export function getManifestPath() {
  return resolve(getReleaseRoot(), 'release-manifest.json');
}

export function getChecksumsPath() {
  return resolve(getReleaseRoot(), 'checksums.json');
}

export function getSignaturePath() {
  return resolve(getReleaseRoot(), 'signature.json');
}

export function getReceiptPath() {
  return resolve(getReleaseRoot(), 'constitutional-release-receipt.json');
}

export function getBundleManifestPath() {
  return resolve(getBundleRoot(), 'release-package.json');
}

export function getBundleChecksumsPath() {
  return resolve(getBundleRoot(), 'checksums.json');
}

export function getBundleSignaturePath() {
  return resolve(getBundleRoot(), 'signature.json');
}

export function getBundleReceiptPath() {
  return resolve(getBundleRoot(), 'constitutional-release-receipt.json');
}

export function readJson(filePath, fallback) {
  if (!existsSync(filePath)) {
    return fallback;
  }
  const raw = readFileSync(filePath, 'utf8');
  if (!raw.trim()) {
    return fallback;
  }
  return JSON.parse(raw);
}

export function writeJson(filePath, value) {
  mkdirSync(dirname(filePath), { recursive: true });
  writeFileSync(filePath, `${JSON.stringify(value, null, 2)}\n`, { encoding: 'utf8' });
}

export function ensureDir(dirPath) {
  mkdirSync(dirPath, { recursive: true });
}

export function normalizeArtifactPath(artifactPath) {
  return String(artifactPath).replace(/\\/g, '/').replace(/^\.\//, '');
}

export function loadManifest() {
  const manifest = readJson(getManifestPath(), {
    name: 'aaes-os',
    version: '0.1.0',
    bundle: 'release/bundle',
    artifacts: [],
  });

  const artifacts = Array.isArray(manifest.artifacts)
    ? manifest.artifacts.map(normalizeArtifactPath).filter(Boolean)
    : [];

  return {
    ...manifest,
    artifacts,
  };
}

export function resolveArtifactPath(artifactPath) {
  return resolve(getRepoRoot(), normalizeArtifactPath(artifactPath));
}

export function hashFile(filePath) {
  const content = readFileSync(filePath);
  return createHash('sha256').update(content).digest('hex');
}

export function listBundleFiles(rootDir) {
  if (!existsSync(rootDir)) {
    return [];
  }

  const entries = [];
  for (const entry of readdirSync(rootDir, { withFileTypes: true })) {
    const entryPath = resolve(rootDir, entry.name);
    if (entry.isDirectory()) {
      entries.push(...listBundleFiles(entryPath));
    } else if (entry.isFile()) {
      entries.push(entryPath);
    }
  }
  return entries;
}

export function copyArtifactTree(sourcePath, bundleRoot, relativePath) {
  const targetPath = resolve(bundleRoot, relativePath);
  ensureDir(dirname(targetPath));
  copyFileSync(sourcePath, targetPath);
  return targetPath;
}

export function getArtifactRecords(manifest) {
  return manifest.artifacts.map((artifactPath) => {
    const absolutePath = resolveArtifactPath(artifactPath);
    if (!existsSync(absolutePath)) {
      throw new Error(`Missing release artifact: ${artifactPath}`);
    }

    const stats = statSync(absolutePath);
    if (!stats.isFile()) {
      throw new Error(`Release artifact is not a file: ${artifactPath}`);
    }

    return {
      path: normalizeArtifactPath(artifactPath),
      absolutePath,
      size: stats.size,
      sha256: hashFile(absolutePath),
    };
  });
}

export function computeSignature(records, manifest) {
  const hash = createHash('sha256');
  hash.update(JSON.stringify({ name: manifest.name, version: manifest.version, bundle: manifest.bundle }, null, 2));
  for (const record of records) {
    hash.update(record.path);
    hash.update(record.sha256);
    hash.update(String(record.size));
  }
  return hash.digest('hex');
}
