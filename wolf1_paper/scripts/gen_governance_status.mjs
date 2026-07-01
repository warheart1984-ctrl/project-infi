import fs from 'fs';
import path from 'path';
import { ROOT } from './lib/paths.mjs';

const receiptsPath = path.join(ROOT, 'governance', 'receipts-index.json');
const adrDir = path.join(ROOT, 'adr');
const amendDir = path.join(ROOT, 'amendments');
const outPath = path.join(ROOT, 'governance', 'governance-status.json');

let receipts = [];
if (fs.existsSync(receiptsPath)) {
  receipts = JSON.parse(fs.readFileSync(receiptsPath, 'utf8'));
}

const docIds = new Set(receipts.map((r) => r.document_id).filter(Boolean));
const adrs = fs.existsSync(adrDir)
  ? fs.readdirSync(adrDir).filter((f) => /^ADR-/.test(f) && f.endsWith('.md'))
  : [];

let ctsStatus = 'PASS';
try {
  const { spawnSync } = await import('child_process');
  const r = spawnSync(process.execPath, ['cts/run_all.mjs'], { cwd: ROOT, encoding: 'utf8' });
  if (r.status !== 0) ctsStatus = 'FAIL';
} catch {
  ctsStatus = 'UNKNOWN';
}

const status = {
  cts_status: ctsStatus,
  documents_built: docIds.size,
  open_adrs: adrs.length,
  last_updated: new Date().toISOString().replace(/\.\d{3}Z$/, 'Z'),
};

fs.writeFileSync(outPath, JSON.stringify(status, null, 2) + '\n', 'utf8');
console.log('[GOV-STATUS] Wrote', path.relative(ROOT, outPath), status);
