#!/usr/bin/env tsx
/**
 * Validate Production Baseline OEL evidence with @aaes-os/cef-core.
 * Exit 0 only when schema + invariants pass and promotion is not overclaiming.
 */
import { readFileSync, writeFileSync } from 'node:fs';
import { resolve } from 'node:path';
import {
  allInvariantsPassed,
  assertPromotionAllowed,
  validateEvidence,
  validateProfile,
} from '@aaes-os/cef-core';

const defaultEvidence =
  'docs/release/production-baseline/aaes-os-v1.0/evidence/oel-evidence-validated.json';
const defaultReceipt =
  'docs/release/production-baseline/aaes-os-v1.0/evidence/cef-core-validation-receipt.json';

function main() {
  const evidencePath = resolve(process.argv[2] ?? defaultEvidence);
  const receiptPath = resolve(process.argv[3] ?? defaultReceipt);
  const evidence = JSON.parse(readFileSync(evidencePath, 'utf8')) as unknown;

  const core = validateEvidence(evidence);
  const profile = validateProfile('OEL', evidence);
  const invariants = allInvariantsPassed(evidence);
  const promotion = assertPromotionAllowed(evidence);

  const receipt = {
    kind: 'cef-core-validation-receipt',
    baselineId: 'AAES-OS-PRODUCTION-BASELINE-v1.0',
    evidenceRef: evidencePath.replace(/\\/g, '/'),
    package: '@aaes-os/cef-core',
    packageVersion: '1.0.0',
    validatedAt: new Date().toISOString(),
    checks: {
      validateEvidence: core.valid,
      validateProfileOEL: profile.valid,
      allInvariantsPassed: invariants,
      promotionAllowed: promotion.allowed,
      promotionReason: promotion.reason,
    },
    promotionImplication: promotion.allowed
      ? 'Promotion structurally allowed; still requires authority signature + live digests/cluster evidence for ACTIVE certificate'
      : `Promotion blocked: ${promotion.reason}`,
  };

  writeFileSync(receiptPath, `${JSON.stringify(receipt, null, 2)}\n`, 'utf8');
  console.log(JSON.stringify(receipt, null, 2));

  if (!core.valid || !profile.valid || !invariants) {
    process.exit(1);
  }
}

main();
