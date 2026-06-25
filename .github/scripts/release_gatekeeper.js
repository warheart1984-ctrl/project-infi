#!/usr/bin/env node

/**
 * AAES-OS Release Gatekeeper
 * Blocks merges when release gates are not satisfied.
 *
 * Set AAES_RELEASE_STRICT=1 to enforce evidence-ledger hypothesis checks.
 * CI writes results to aaes-os/.ci/*.json via scripts/write-ci-results.mjs
 */

import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const repoRoot = path.resolve(__dirname, '../..');
const aaesRoot = path.join(repoRoot, 'aaes-os');
const ciDir = path.join(aaesRoot, '.ci');

function fail(msg) {
  console.error('RELEASE GATE FAILED:');
  console.error(msg);
  process.exit(1);
}

function pass(msg) {
  console.log('OK ' + msg);
}

function readJson(name) {
  const file = path.join(ciDir, name);
  if (!fs.existsSync(file)) {
    fail(`Missing CI artifact: ${file}. Run aaes-os/scripts/write-ci-results.mjs first.`);
  }
  return JSON.parse(fs.readFileSync(file, 'utf8'));
}

// 1. CTS
const ctsResults = readJson('cts_results.json');
if (!ctsResults.allPassed) {
  fail('CTS tests did not pass.');
}
pass('CTS tests passed.');

// 2. Determinism
const detResults = readJson('determinism_results.json');
if (!detResults.deterministic) {
  fail('Determinism tests failed.');
}
pass('Determinism verified.');

// 3. Governance
const govResults = readJson('governance_results.json');
if (!govResults.allPassed) {
  fail('Governance tests failed.');
}
pass('Governance tests passed.');

// 4. Evidence ledger (strict mode only — v1.0 not ready until claims graduate)
if (process.env.AAES_RELEASE_STRICT === '1') {
  const ledgerPath = path.join(aaesRoot, 'EVIDENCE_LEDGER.md');
  const ledger = fs.readFileSync(ledgerPath, 'utf8');
  const requiredClaims = [
    'CRK-1 produces deterministic receipts',
    'CAS 1.0 is fully specified',
    'Governance Engine enforces invariants',
  ];
  for (const claim of requiredClaims) {
    const row = ledger
      .split('\n')
      .find((line) => line.includes(claim) && line.startsWith('|'));
    if (row && /\|\s*Hypothesis\s*\|/i.test(row)) {
      fail(`Evidence level for claim "${claim}" is still Hypothesis.`);
    }
  }
  pass('Evidence Ledger validated (strict).');
} else {
  console.log('SKIP Evidence Ledger strict check (set AAES_RELEASE_STRICT=1 to enable).');
}

// 5. Architectural drift — constitution must not document forbidden expansions
const constitutionPath = path.join(
  repoRoot,
  'docs/aaes-os/governance/CONSTITUTION.md',
);
if (fs.existsSync(constitutionPath)) {
  const constitution = fs.readFileSync(constitutionPath, 'utf8').toLowerCase();
  const forbidden = [
    'approved new invariant',
    'added new constitutional object',
    'new governance surface added',
  ];
  for (const term of forbidden) {
    if (constitution.includes(term)) {
      fail(`Forbidden architectural change detected in constitution: ${term}`);
    }
  }
  pass('No architectural drift detected in constitution.');
}

console.log('All release gates satisfied. Merge allowed.');
process.exit(0);
