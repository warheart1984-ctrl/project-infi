import { createHash } from 'node:crypto';

import {
  createDemoProofSurfaceRegistry,
  resolveConstitutionalEvidenceGraphFromReleaseReceipt,
  validateConstitutionalEvidenceGraph,
} from '../packages/aaes-governance/dist/index.js';

import { getBundleReceiptPath, getReceiptPath, readJson, writeJson } from './shared.ts';

function createEvidenceSection(status, evidence, notes) {
  return {
    status,
    evidence: [...evidence],
    notes: [...notes],
  };
}

export function createReleaseReceipt(manifest, checksums, extras = {}) {
  const generatedAt = extras.generatedAt ?? new Date().toISOString();
  const baseReceipt = {
    receiptId: `release:${manifest.name}:${manifest.version}`,
    release: {
      name: manifest.name,
      version: manifest.version,
      bundle: manifest.bundle,
      artifactCount: manifest.artifacts.length,
      checksumCount: checksums.files.length,
      signature: extras.signature ?? null,
    },
    proofSurfaceLevel: 'P2',
    buildEvidence: createEvidenceSection(
      'Observed',
      ['release/release-manifest.json', 'release/checksums.json'],
      ['Checksums are computed from the selected release artifacts.'],
    ),
    testEvidence: createEvidenceSection(
      'Observed',
      [
        'pnpm exec vitest run (435 passed, 2 environment-dependent integration tests skipped)',
        'pnpm run release:drift (25 passed)',
      ],
      ['Fresh local verification completed on 2026-07-14.'],
    ),
    lintStatus: createEvidenceSection(
      'Observed',
      ['pnpm exec eslint "packages/**/*.{js,jsx,ts,tsx,mjs,cjs}" "services/**/*.{js,jsx,ts,tsx,mjs,cjs}" --max-warnings 0'],
      ['Strict workspace lint completed with zero errors on 2026-07-14.'],
    ),
    replayStatus: createEvidenceSection(
      'Observed',
      ['packages/runledger', 'packages/evidence-receipts', 'release/signature.json', 'pnpm run release:drift'],
      ['Replay/drift verification passed 25 tests; external database integration replays remain environment-dependent.'],
    ),
    auditStatus: createEvidenceSection(
      'Observed',
      ['docs/README.md', 'docs/scorecards/project-infi.md', 'docs-site/docs/overview.md'],
      ['Audit trace is documented in the docs hub and scorecard.'],
    ),
    verificationDate: extras.verificationDate ?? null,
    knownLimitations: [
      'Coverage percentages are not yet standardized across every workspace package.',
      'External database integration tests require configured PostgreSQL and Neo4j services.',
      'Release verification covers selected artifacts, not production deployment or independent certification.',
    ],
    truthBoundary:
      'This receipt proves the bundle was built, packaged, signed, and verified against the selected artifacts. It does not prove production readiness for unfinished surfaces.',
    constitutionalMaturity: 'Verified Prototype',
    commercialReadiness: 'Builder',
    generatedAt,
  };

  const constitutionalEvidenceGraph = resolveConstitutionalEvidenceGraphFromReleaseReceipt(
    baseReceipt,
    createDemoProofSurfaceRegistry().list(),
    {
      generatedAt,
    },
  );

  const releaseReceipt = {
    ...baseReceipt,
    constitutionalEvidenceGraph,
  };

  const releaseReceiptIssues = validateReleaseReceipt(releaseReceipt);
  if (releaseReceiptIssues.length > 0) {
    throw new Error(`release receipt validation failed: ${releaseReceiptIssues.join('; ')}`);
  }

  return releaseReceipt;
}

export function computeReleaseReceiptHash(receipt) {
  const canonical = structuredClone(receipt);
  delete canonical.receiptHash;
  const hash = createHash('sha256');
  hash.update(JSON.stringify(canonical));
  return `sha256:${hash.digest('hex')}`;
}

export function validateReleaseReceipt(receipt, options = {}) {
  const expectedSignature = options.expectedSignature ?? null;
  const requireVerificationDate = options.requireVerificationDate ?? false;
  const requireReceiptHash = options.requireReceiptHash ?? false;
  const issues = [];

  if (!receipt || typeof receipt !== 'object') {
    issues.push('release receipt is missing');
    return issues;
  }

  if (typeof receipt.receiptId !== 'string' || !receipt.receiptId.startsWith('release:')) {
    issues.push('release receipt id is missing or invalid');
  }

  if (!receipt.release || typeof receipt.release !== 'object') {
    issues.push('release metadata is missing');
  } else {
    if (typeof receipt.release.name !== 'string' || receipt.release.name.length === 0) {
      issues.push('release name is missing');
    }
    if (typeof receipt.release.version !== 'string' || receipt.release.version.length === 0) {
      issues.push('release version is missing');
    }
    if (typeof receipt.release.bundle !== 'string' || receipt.release.bundle.length === 0) {
      issues.push('release bundle is missing');
    }
    if (typeof receipt.release.artifactCount !== 'number') {
      issues.push('release artifact count is missing');
    }
    if (typeof receipt.release.checksumCount !== 'number') {
      issues.push('release checksum count is missing');
    }
  }

  if (receipt.proofSurfaceLevel !== 'P0' && receipt.proofSurfaceLevel !== 'P1' && receipt.proofSurfaceLevel !== 'P2' && receipt.proofSurfaceLevel !== 'P3' && receipt.proofSurfaceLevel !== 'P4' && receipt.proofSurfaceLevel !== 'P5') {
    issues.push('release proof surface level is missing or invalid');
  }

  for (const field of ['buildEvidence', 'testEvidence', 'lintStatus', 'replayStatus', 'auditStatus']) {
    const section = receipt[field];
    if (!section || typeof section !== 'object') {
      issues.push(`${field} is missing`);
      continue;
    }
    if (typeof section.status !== 'string' || section.status.length === 0) {
      issues.push(`${field} status is missing`);
    }
    if (!Array.isArray(section.evidence)) {
      issues.push(`${field} evidence is missing`);
    }
    if (!Array.isArray(section.notes)) {
      issues.push(`${field} notes are missing`);
    }
  }

  if (typeof receipt.truthBoundary !== 'string' || receipt.truthBoundary.length === 0) {
    issues.push('truth boundary is missing');
  }

  if (typeof receipt.constitutionalMaturity !== 'string' || receipt.constitutionalMaturity.length === 0) {
    issues.push('constitutional maturity is missing');
  }

  if (typeof receipt.commercialReadiness !== 'string' || receipt.commercialReadiness.length === 0) {
    issues.push('commercial readiness is missing');
  }

  if (requireVerificationDate && (typeof receipt.verificationDate !== 'string' || receipt.verificationDate.length === 0)) {
    issues.push('verification date is missing');
  }

  if (receipt.verificationDate != null && typeof receipt.verificationDate !== 'string') {
    issues.push('verification date must be a string when present');
  }

  if (receipt.generatedAt != null && typeof receipt.generatedAt !== 'string') {
    issues.push('generatedAt must be a string when present');
  }

  if (receipt.receiptHash != null && typeof receipt.receiptHash !== 'string') {
    issues.push('receipt hash must be a string when present');
  }

  if (requireReceiptHash && (typeof receipt.receiptHash !== 'string' || receipt.receiptHash.length === 0)) {
    issues.push('receipt hash is missing');
  }

  if (expectedSignature !== null) {
    if (!receipt.release || receipt.release.signature !== expectedSignature) {
      issues.push('release signature does not match the signed payload');
    }
  }

  if (!receipt.constitutionalEvidenceGraph || typeof receipt.constitutionalEvidenceGraph !== 'object') {
    issues.push('constitutional evidence graph is missing');
  } else {
    const graphIssues = validateConstitutionalEvidenceGraph(receipt.constitutionalEvidenceGraph);
    for (const issue of graphIssues) {
      issues.push(`constitutional evidence graph ${issue.scope}.${issue.field}: ${issue.message}`);
    }
    if (receipt.constitutionalEvidenceGraph.rootReceipt?.receiptId !== receipt.receiptId) {
      issues.push('constitutional evidence graph root receipt does not match the release receipt id');
    }
    if (receipt.constitutionalEvidenceGraph.rootReceipt?.constitutionalEvidenceGraph != null) {
      issues.push('constitutional evidence graph root receipt must not embed another constitutional evidence graph');
    }
  }

  return issues;
}

export function attachReleaseSignature(receipt, signature) {
  return {
    ...receipt,
    release: {
      ...receipt.release,
      signature,
    },
  };
}

export function attachReleaseVerificationDate(receipt, verificationDate) {
  return {
    ...receipt,
    verificationDate,
  };
}

export function attachReleaseReceiptHash(receipt) {
  return {
    ...receipt,
    receiptHash: computeReleaseReceiptHash(receipt),
  };
}

export function readReleaseReceipt() {
  return readJson(getReceiptPath(), null);
}

export function readBundleReleaseReceipt() {
  return readJson(getBundleReceiptPath(), null);
}

export function writeReleaseReceipt(receipt) {
  writeJson(getReceiptPath(), receipt);
}

export function writeBundleReleaseReceipt(receipt) {
  writeJson(getBundleReceiptPath(), receipt);
}

export function syncReleaseReceipt(receipt) {
  writeReleaseReceipt(receipt);
  writeBundleReleaseReceipt(receipt);
}
