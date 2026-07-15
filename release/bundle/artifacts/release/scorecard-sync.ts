import { readFileSync, writeFileSync } from 'node:fs';
import { resolve } from 'node:path';

import { getBundleRoot, getRepoRoot } from './shared.ts';

function buildReceiptDrivenSnapshot(receipt) {
  const maturity = String(receipt?.constitutionalMaturity ?? 'Unknown');
  const proofSurfaceLevel = String(receipt?.proofSurfaceLevel ?? 'P0');
  const commercialReadiness = String(receipt?.commercialReadiness ?? 'Unknown');
  const receiptHash = String(receipt?.receiptHash ?? 'pending release verification');
  const verificationTimestamp = String(receipt?.verificationDate ?? 'pending release verification');

  return {
    currentMaturity: `${maturity} for the governance/runtime spine, docs-site, Nova Studio, ops-console, and SovereignX execution surfaces; scaffold / prototype elsewhere.`,
    proofSurfaceOperationalStatus: `${maturity} for the governance/runtime spine, docs-site, ops surfaces, Nova Studio, and SovereignX execution surfaces; other surfaces remain scaffold/prototype.`,
    proofSurfaceLevel: `${proofSurfaceLevel}-Verified for the governed baseline; lower levels apply to unfinished surfaces.`,
    commercialReadiness: `${commercialReadiness} tier with prototype-to-verified-prototype progression.`,
    receiptHash,
    verificationTimestamp,
  };
}

function replaceAny(content, candidates, to, filePath) {
  for (const from of candidates) {
    if (content.includes(from)) {
      return content.replace(from, to);
    }
  }

  if (content.includes(to)) {
    return content;
  }

  if (!candidates.length) {
    throw new Error(`no replacement candidates were provided for ${filePath}`);
  }

  throw new Error(`expected text not found in ${filePath}`);
}

function updateReadme(filePath, snapshot) {
  const content = readFileSync(filePath, 'utf8');
  let updated = content;

  updated = replaceAny(
    updated,
    [
      '| Layer 0 - Constitutional Ontology | Defines the constitutional vocabulary for Authority, Evidence, Verification, Compliance, and Truth |',
    ],
    `| Layer 0 - Constitutional Ontology | Defines the constitutional vocabulary for Authority, Evidence, Verification, Compliance, and Truth |`,
    filePath,
  );
  updated = replaceAny(
    updated,
    [
      '| Current maturity | Verified Prototype for the governance/runtime spine, docs-site, Nova Studio, and ops-console surfaces; scaffold / prototype elsewhere. |',
      '| Current maturity | Verified Prototype for the governance/runtime spine, docs-site, Nova Studio, and ops-console surfaces; scaffold / prototype elsewhere |',
      '| Current maturity | Verified Prototype for the governance/runtime spine, docs-site, Nova Studio, ops-console, and SovereignX execution surfaces; scaffold / prototype elsewhere. |',
      '| Current maturity | Verified Prototype for the governance/runtime spine, docs-site, Nova Studio, ops-console, and SovereignX execution surfaces; scaffold / prototype elsewhere |',
      '| Current maturity | Verified Prototype for the governance/runtime spine, docs-site, Nova Studio, ops-console, and SovereignX execution surfaces; scaffold / prototype elsewhere under the Project Infinity umbrella. |',
    ],
    `| Current maturity | ${snapshot.currentMaturity} |`,
    filePath,
  );
  updated = replaceAny(
    updated,
    [
      '| Operational Status | Verified Prototype for the governance/runtime spine, docs-site, ops surfaces, and Nova Studio; other surfaces remain scaffold/prototype. |',
      '| Operational Status | Verified Prototype for the governance/runtime spine, docs-site, ops surfaces, and Nova Studio; other surfaces remain scaffold/prototype |',
      '| Operational Status | Verified Prototype for the governance/runtime spine, docs-site, ops surfaces, Nova Studio, and SovereignX execution surfaces; other surfaces remain scaffold/prototype. |',
      '| Operational Status | Verified Prototype for the governance/runtime spine, docs-site, ops surfaces, Nova Studio, and SovereignX execution surfaces; other surfaces remain scaffold/prototype |',
      '| Operational Status | Verified Prototype for the governance/runtime spine, docs-site, ops surfaces, Nova Studio, and SovereignX execution surfaces; other surfaces remain scaffold/prototype within the Project Infinity umbrella. |',
    ],
    `| Operational Status | ${snapshot.proofSurfaceOperationalStatus} |`,
    filePath,
  );
  updated = replaceAny(
    updated,
    [
      '| Commercial Readiness | Builder tier with prototype-to-verified-prototype progression. |',
      '| Commercial Readiness | Builder tier with prototype-to-verified-prototype progression |',
    ],
    `| Commercial Readiness | ${snapshot.commercialReadiness} |`,
    filePath,
  );
  updated = updated.split('| Commercial Readiness | Builder tier with prototype-to-verified-prototype progression. |').join(
    `| Commercial Readiness | ${snapshot.commercialReadiness} |`,
  );
  updated = replaceAny(
    updated,
    [
      '| Proof Level | P2-Verified for the governed baseline; lower levels apply to unfinished surfaces. |',
      '| Proof Level | P2-Verified for the governed baseline; lower levels apply to unfinished surfaces |',
    ],
    `| Proof Level | ${snapshot.proofSurfaceLevel} |`,
    filePath,
  );
  updated = updated.replace(/\| Receipt hash \| .* \|/g, `| Receipt hash | ${snapshot.receiptHash} |`);
  if (updated === content || !updated.includes(snapshot.receiptHash)) {
    throw new Error(`expected text not found in ${filePath}`);
  }
  updated = updated.replace(
    /\| Verification timestamp \| .* \|/g,
    `| Verification timestamp | ${snapshot.verificationTimestamp} |`,
  );

  if (updated !== content) {
    writeFileSync(filePath, `${updated}\n`);
  }
}

function updateScorecard(filePath, snapshot) {
  const content = readFileSync(filePath, 'utf8');
  let updated = content;

  updated = replaceAny(
    updated,
    [
      '| Layer 0 - Constitutional Ontology | Defines the constitutional vocabulary for Authority, Evidence, Verification, Compliance, and Truth |',
    ],
    `| Layer 0 - Constitutional Ontology | Defines the constitutional vocabulary for Authority, Evidence, Verification, Compliance, and Truth |`,
    filePath,
  );
  updated = replaceAny(
    updated,
    [
      '| Current maturity | Verified Prototype for the governance/runtime spine, docs-site, Nova Studio, and ops-console surfaces; scaffold / prototype elsewhere. |',
      '| Current maturity | Verified Prototype for the governance/runtime spine, docs-site, Nova Studio, and ops-console surfaces; scaffold / prototype elsewhere |',
    ],
    `| Current maturity | ${snapshot.currentMaturity} |`,
    filePath,
  );
  updated = replaceAny(
    updated,
    [
      'Verified Prototype for the governance spine, operational backend, and Nova Studio build/smoke surface. Other surfaces remain scaffold or prototype quality until their build, docs, and smoke paths are explicitly finished.',
      'Verified Prototype for the governance/runtime spine, docs-site, Nova Studio, and ops-console surfaces; scaffold / prototype elsewhere.',
      'Verified Prototype for the governance/runtime spine, docs-site, Nova Studio, ops-console, and SovereignX execution surfaces; scaffold / prototype elsewhere.',
    ],
    snapshot.currentMaturity,
    filePath,
  );
  updated = replaceAny(
    updated,
    [
      'Verified Prototype for the governance spine, docs-site, and Nova Studio surfaces, Prototype for several runtime packages, Scaffold for unfinished runtime work.',
      'Verified Prototype for the governance/runtime spine, docs-site, Nova Studio, and ops-console surfaces; scaffold / prototype elsewhere.',
      'Verified Prototype for the governance/runtime spine, docs-site, Nova Studio, ops-console, and SovereignX execution surfaces; scaffold / prototype elsewhere.',
    ],
    snapshot.currentMaturity,
    filePath,
  );
  updated = replaceAny(
    updated,
    [
      'Verified Prototype for the governance spine, operational backend, and Nova Studio; scaffold or prototype elsewhere until fresh proof exists.',
      'Verified Prototype for the governance/runtime spine, docs-site, ops surfaces, and Nova Studio; other surfaces remain scaffold/prototype.',
      'Verified Prototype for the governance/runtime spine, docs-site, ops surfaces, Nova Studio, and SovereignX execution surfaces; other surfaces remain scaffold/prototype.',
    ],
    snapshot.proofSurfaceOperationalStatus,
    filePath,
  );
  updated = replaceAny(
    updated,
    [
      'P2 for the governed baseline, with lower levels applied to unfinished surfaces.',
      'P2-Verified for the governed baseline; lower levels apply to unfinished surfaces.',
    ],
    snapshot.proofSurfaceLevel,
    filePath,
  );
  updated = replaceAny(
    updated,
    [
      'Builder tier with prototype-to-verified-prototype progression.',
      'Builder tier with prototype-to-verified-prototype progression',
    ],
    snapshot.commercialReadiness,
    filePath,
  );
  updated = updated.replace(/^\| Receipt hash \| .* \|$/m, `| Receipt hash | ${snapshot.receiptHash} |`);
  updated = updated.replace(
    /^\| Verification timestamp \| .* \|$/m,
    `| Verification timestamp | ${snapshot.verificationTimestamp} |`,
  );

  if (updated !== content) {
    writeFileSync(filePath, `${updated}\n`);
  }
}

function updateOverview(filePath, snapshot) {
  const content = readFileSync(filePath, 'utf8');
  let updated = content;

  updated = replaceAny(
    updated,
    [
      '- Layer 0 - Constitutional Ontology: Defines the constitutional vocabulary for Authority, Evidence, Verification, Compliance, and Truth.',
      '- Layer 0 - Constitutional Ontology: Defines the constitutional vocabulary for Authority, Evidence, Verification, Compliance, and Truth',
    ],
    `- Layer 0 - Constitutional Ontology: Defines the constitutional vocabulary for Authority, Evidence, Verification, Compliance, and Truth.`,
    filePath,
  );
  updated = replaceAny(
    updated,
    [
      '- Current maturity: Verified Prototype for the governance/runtime spine, docs-site, Nova Studio, and ops-console surfaces; scaffold / prototype elsewhere.',
      '- Current maturity: Verified Prototype for the governance/runtime spine, docs-site, Nova Studio, and ops-console surfaces; scaffold / prototype elsewhere',
    ],
    `- Current maturity: ${snapshot.currentMaturity}`,
    filePath,
  );
  updated = replaceAny(
    updated,
    [
      '- Operational status: Verified Prototype for the governance/runtime spine, docs-site, ops surfaces, and Nova Studio; other surfaces remain scaffold/prototype.',
      '- Operational status: Verified Prototype for the governance/runtime spine, docs-site, ops surfaces, and Nova Studio; other surfaces remain scaffold/prototype',
    ],
    `- Operational status: ${snapshot.proofSurfaceOperationalStatus}`,
    filePath,
  );
  updated = replaceAny(
    updated,
    [
      '- Commercial readiness: Builder tier with prototype-to-verified-prototype progression.',
      '- Commercial readiness: Builder tier with prototype-to-verified-prototype progression',
    ],
    `- Commercial readiness: ${snapshot.commercialReadiness}`,
    filePath,
  );
  updated = replaceAny(
    updated,
    [
      '- Proof level: P2-Verified for the governed baseline; lower levels apply to unfinished surfaces.',
      '- Proof level: P2-Verified for the governed baseline; lower levels apply to unfinished surfaces',
    ],
    `- Proof level: ${snapshot.proofSurfaceLevel}`,
    filePath,
  );
  updated = updated.replace(/^- Receipt hash: .*$/m, `- Receipt hash: ${snapshot.receiptHash}`);
  if (!updated.includes(snapshot.receiptHash)) {
    throw new Error(`expected text not found in ${filePath}`);
  }
  updated = updated.replace(
    /^- Verification timestamp: .*$/m,
    `- Verification timestamp: ${snapshot.verificationTimestamp}`,
  );

  if (updated !== content) {
    writeFileSync(filePath, `${updated}\n`);
  }
}

export function syncScorecardSnapshot(receipt) {
  const snapshot = buildReceiptDrivenSnapshot(receipt);
  const targets = [
    { path: resolve(getRepoRoot(), 'README.md'), kind: 'readme' },
    { path: resolve(getRepoRoot(), 'docs/scorecards/project-infi.md'), kind: 'scorecard' },
    { path: resolve(getRepoRoot(), 'docs-site/docs/overview.md'), kind: 'overview' },
    { path: resolve(getBundleRoot(), 'artifacts/README.md'), kind: 'readme' },
    { path: resolve(getBundleRoot(), 'artifacts/docs/scorecards/project-infi.md'), kind: 'scorecard' },
  ];

  for (const target of targets) {
    if (target.kind === 'readme') {
      updateReadme(target.path, snapshot);
    } else if (target.kind === 'overview') {
      updateOverview(target.path, snapshot);
    } else {
      updateScorecard(target.path, snapshot);
    }
  }
}
