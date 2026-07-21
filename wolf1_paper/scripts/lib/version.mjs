import fs from 'fs';
import path from 'path';
import { parse } from 'yaml';
import { ROOT } from './paths.mjs';

const VERSION_FILE = path.join(ROOT, '.governance', 'version.yaml');

export function loadManifest() {
  const raw = fs.readFileSync(VERSION_FILE, 'utf8');
  return parse(raw);
}

export function getDocument(docId) {
  const manifest = loadManifest();
  const doc = manifest.documents?.find((d) => d.id === docId);
  if (!doc) {
    throw new Error(`Document "${docId}" not found in ${VERSION_FILE}`);
  }
  return doc;
}

export function resolveFromRoot(relativePath) {
  return path.join(ROOT, relativePath);
}
