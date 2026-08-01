#!/usr/bin/env tsx
/**
 * Merge per-service digest JSON files into Production Baseline image-tags.json.
 *
 * Usage:
 *   tsx tools/merge-image-digests.ts --digests-dir ./digests [--out path]
 */
import { readdirSync, readFileSync, writeFileSync, existsSync } from 'node:fs';
import { join, resolve } from 'node:path';

type DigestFile = {
  service: string;
  digest: string;
  image?: string;
  gitSha?: string;
  runId?: string | number;
};

type ImageTagsDoc = {
  baselineId: string;
  kind: string;
  frozenCommit: string;
  registry: string;
  policy: Record<string, unknown>;
  services: Array<{
    service: string;
    imageRepository: string;
    baselineTagCandidates: string[];
    digest: string | null;
    digestStatus: string;
  }>;
  pinningExample: string;
  truthBoundary: string;
  lastDigestMergeAt?: string;
  lastDigestMergeSha?: string;
  lastDigestMergeRunId?: string;
};

function parseArgs(argv: string[]) {
  let digestsDir = '';
  let out =
    'docs/release/production-baseline/aaes-os-v1.0/evidence/image-tags.json';
  for (let i = 0; i < argv.length; i++) {
    if (argv[i] === '--digests-dir') digestsDir = argv[++i] ?? '';
    if (argv[i] === '--out') out = argv[++i] ?? out;
  }
  if (!digestsDir) {
    console.error('Usage: merge-image-digests.ts --digests-dir <dir> [--out path]');
    process.exit(2);
  }
  return { digestsDir: resolve(digestsDir), out: resolve(out) };
}

function loadDigests(dir: string): DigestFile[] {
  if (!existsSync(dir)) {
    throw new Error(`digests dir missing: ${dir}`);
  }
  const files = readdirSync(dir).filter((f) => f.endsWith('.json'));
  return files.map((f) => {
    const raw = JSON.parse(readFileSync(join(dir, f), 'utf8')) as DigestFile;
    if (!raw.service || !raw.digest) {
      throw new Error(`invalid digest file ${f}: need service + digest`);
    }
    if (!raw.digest.startsWith('sha256:')) {
      throw new Error(`digest for ${raw.service} must start with sha256:`);
    }
    return raw;
  });
}

function main() {
  const { digestsDir, out } = parseArgs(process.argv.slice(2));
  const digests = loadDigests(digestsDir);
  const byService = new Map(digests.map((d) => [d.service, d]));

  const doc = JSON.parse(readFileSync(out, 'utf8')) as ImageTagsDoc;
  let filled = 0;
  for (const svc of doc.services) {
    const d = byService.get(svc.service);
    if (!d) continue;
    svc.digest = d.digest;
    svc.digestStatus = 'ci-emitted';
    filled++;
  }

  const sample = digests[0];
  doc.lastDigestMergeAt = new Date().toISOString();
  if (sample?.gitSha) doc.lastDigestMergeSha = sample.gitSha;
  if (sample?.runId != null) doc.lastDigestMergeRunId = String(sample.runId);
  doc.truthBoundary =
    filled === doc.services.length
      ? 'Tag policy frozen; all service digests filled from CI digest artifacts.'
      : `Tag policy frozen; ${filled}/${doc.services.length} digests filled from CI. Remaining services stay pending-first-ghcr-push until emitted.`;

  writeFileSync(out, `${JSON.stringify(doc, null, 2)}\n`, 'utf8');
  console.log(
    JSON.stringify(
      {
        out,
        filled,
        total: doc.services.length,
        services: digests.map((d) => d.service),
      },
      null,
      2,
    ),
  );
  if (filled === 0) process.exit(1);
}

main();
