import express from 'express';
import { existsSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

import { DriftMetrics } from '@aaes-os/aaes-governance';
import { createCenDemoResult, type EnforcementReceipt } from '@aaes-os/constitutional-enforcement-node';
import {
  evaluateInvariantFitness,
  proposeInvariant,
} from '@aaes-os/constitutional-evolution';
import {
  collapseGovernanceLayers,
  createLawOfLawsLedger,
  recordMetaConstitutionalCollapsePod,
} from '@aaes-os/meta-constitutional-calculus';
import { forecastTrajectory } from '@aaes-os/nimf';
import {
  appendSovereigntyEntry,
  createSovereigntyLedger,
} from '@aaes-os/sovereignty-ledger';

import {
  approvePatch,
  deployPatch,
  listPatches,
  rejectPatch,
} from './patchLedgerState.js';
import { getSeededMriAssessment, getSeededMriAssessmentV2 } from './mriState.js';
import {
  ensureTelemetrySeeded,
  faultJournal,
  patchAnalytics,
  patternLedger,
} from './telemetryState.js';
import { getSubsystemCoverage } from './coverageState.js';
import { getCabTelemetrySummary } from './cabTelemetry.js';
import { getAaisTelemetryStatus } from './aaisBridge.js';

const PORT = Number(process.env.PORT ?? 4000);
const serviceDir = path.dirname(fileURLToPath(import.meta.url));
const clientDistDir = path.resolve(serviceDir, '..', 'dist', 'client');

ensureTelemetrySeeded();

const seededCenResult = createCenDemoResult();
const sovereigntyLedger = createSovereigntyLedger();
appendSovereigntyEntry(sovereigntyLedger, {
  eventType: 'denied_transition',
  subjectId: seededCenResult.receipt.transitionId,
  payload: seededCenResult.receipt,
  issuedAt: seededCenResult.receipt.issuedAt,
});
const lawOfLawsLedger = createLawOfLawsLedger();
lawOfLawsLedger.append({
  entryType: 'collapse_record',
  subjectId: 'CML-15',
  payload: collapseGovernanceLayers(),
  issuedAt: '2026-06-18T22:02:00.000Z',
});
lawOfLawsLedger.append({
  entryType: 'pod',
  subjectId: 'meta_constitutional_collapse',
  payload: recordMetaConstitutionalCollapsePod(),
  issuedAt: '2026-06-18T22:02:01.000Z',
});
const cenReceipts = new Map<string, EnforcementReceipt>([
  [seededCenResult.receipt.receiptId, seededCenResult.receipt],
]);

const app = express();
app.use((req, res, next) => {
  const requestId = req.header('x-request-id') ?? `req-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`;
  res.setHeader('x-request-id', requestId);
  res.setHeader('x-content-type-options', 'nosniff');
  res.setHeader('x-frame-options', 'DENY');
  res.setHeader('referrer-policy', 'no-referrer');
  next();
});
app.use(express.json({ limit: '1mb' }));

app.get('/health', (_req, res) => {
  res.json({ ok: true });
});

app.get('/readiness', (_req, res) => {
  const checks = {
    telemetry: faultJournal.getAll().length > 0,
    cen: cenReceipts.size > 0,
    sovereigntyLedger: sovereigntyLedger.entries().length > 0,
    lawOfLawsLedger: lawOfLawsLedger.entries().length > 0,
  };
  res.json({
    ready: Object.values(checks).every(Boolean),
    checks,
  });
});

app.get('/telemetry', async (_req, res) => {
  const faults = faultJournal.getAll();
  const patterns = patternLedger.getAll();
  const drift = new DriftMetrics().computeDrift(faults, patterns);
  const aais = await getAaisTelemetryStatus();
  res.json({
    drift,
    topPatterns: patternLedger.getTopRecurring(5),
    lastFaults: faults.slice(-10).reverse(),
    patchTimeline: patchAnalytics.getTimeline(),
    cab: getCabTelemetrySummary(),
    aais,
  });
});

app.get('/aais/health', async (_req, res) => {
  res.json({ aais: await getAaisTelemetryStatus() });
});

app.get('/mri', (_req, res) => {
  res.json(getSeededMriAssessment());
});

app.get('/mri/v2', (_req, res) => {
  res.json(getSeededMriAssessmentV2());
});

app.get('/coverage', (_req, res) => {
  const coverage = getSubsystemCoverage();
  res.json({
    inventory: coverage.inventory,
    mappedDocuments: coverage.documents.length,
    subsystems: Array.from(new Set(coverage.documents.map((doc) => doc.subsystem))).sort(),
    documents: coverage.documents,
  });
});

app.get('/cen/demo', (_req, res) => {
  res.json(seededCenResult);
});

app.get('/cen/events', (_req, res) => {
  res.json({
    status: 'ACTIVE',
    invariantSet: { active: 6, disabled: 0 },
    tokenCounts: { VT: 1, FT: 1, MRT: 1, RT: 1 },
    enforcementRatePerMinute: 14.2,
    replayAttemptsBlocked: 1,
    events: Array.from(cenReceipts.values()),
  });
});

app.get('/cen/receipts/:receiptId', (req, res) => {
  const receipt = cenReceipts.get(req.params.receiptId);
  if (!receipt) {
    res.status(404).json({ error: 'receipt not found' });
    return;
  }
  res.json({ receipt });
});

app.get('/sovereignty-ledger', (_req, res) => {
  res.json({ entries: sovereigntyLedger.entries() });
});

app.get('/nimf/forecast', (_req, res) => {
  res.json({ forecast: forecastTrajectory(getSeededMriAssessmentV2(), 3) });
});

app.post('/evolution/propose', (req, res) => {
  const body = req.body as { invariantId?: string; expression?: string };
  res.json({
    proposal: proposeInvariant({
      invariantId: body.invariantId ?? 'INV-OPS',
      expression: body.expression ?? 'require governance >= 70',
      mode: 'Genesis',
    }),
  });
});

app.post('/evolution/evaluate', (req, res) => {
  const body = req.body as { invariantId?: string; expression?: string };
  const proposal = proposeInvariant({
    invariantId: body.invariantId ?? 'INV-OPS',
    expression: body.expression ?? 'require governance >= 70',
    mode: 'Genesis',
  });
  res.json({ decision: evaluateInvariantFitness({ proposal, mri: getSeededMriAssessmentV2() }) });
});

app.get('/pod/meta_constitutional_collapse', (_req, res) => {
  res.json({
    pod: recordMetaConstitutionalCollapsePod(),
    collapse: collapseGovernanceLayers(),
  });
});

app.get('/meta/law-of-laws', (_req, res) => {
  res.json({ entries: lawOfLawsLedger.entries() });
});

app.get('/patches', (_req, res) => {
  res.json({ patches: listPatches() });
});

app.post('/patches/:patchId/approve', (req, res) => {
  try {
    const actor = (req.body as { actor?: string })?.actor ?? 'operator';
    const record = approvePatch(req.params.patchId, actor);
    res.json({ patch: record });
  } catch (error) {
    res.status(400).json({ error: error instanceof Error ? error.message : String(error) });
  }
});

app.post('/patches/:patchId/reject', (req, res) => {
  try {
    const record = rejectPatch(req.params.patchId);
    res.json({ patch: record });
  } catch (error) {
    res.status(400).json({ error: error instanceof Error ? error.message : String(error) });
  }
});

app.post('/patches/:patchId/deploy', (req, res) => {
  try {
    const record = deployPatch(req.params.patchId);
    res.json({ patch: record });
  } catch (error) {
    res.status(400).json({ error: error instanceof Error ? error.message : String(error) });
  }
});

if (existsSync(clientDistDir)) {
  app.use(express.static(clientDistDir));
}

app.use((error: unknown, _req: express.Request, res: express.Response, _next: express.NextFunction) => {
  res.status(400).json({ error: error instanceof Error ? error.message : String(error) });
});

if (process.env.NODE_ENV !== 'test') {
  app.listen(PORT, () => {
    console.log(`AAES-OS ops-console listening on http://localhost:${PORT}`);
    console.log(`  GET /telemetry`);
  });
}

export { app };
