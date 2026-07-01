import fs from 'fs';
import path from 'path';
import { ROOT } from './lib/paths.mjs';

const receiptsPath = path.join(ROOT, 'governance', 'receipts-index.json');
const amendDir = path.join(ROOT, 'amendments');
const outPath = path.join(ROOT, 'governance', 'events.json');

const events = [];
let seq = 1;

if (fs.existsSync(receiptsPath)) {
  const receipts = JSON.parse(fs.readFileSync(receiptsPath, 'utf8'));
  for (const r of receipts) {
    events.push({
      id: `EVT-${String(seq++).padStart(4, '0')}`,
      type: 'receipt',
      document_id: r.document_id,
      version: r.version,
      receipt_id: r.receipt_id,
      timestamp: r.timestamp,
      summary: `RECEIPT — ${r.receipt_id ?? r.document_id}`,
    });
  }
}

if (fs.existsSync(amendDir)) {
  const files = fs
    .readdirSync(amendDir)
    .filter((f) => /^amendment-\d+\.md$/.test(f))
    .sort();
  for (const file of files) {
    const text = fs.readFileSync(path.join(amendDir, file), 'utf8');
    const dateMatch = text.match(/\*\*Date:\*\*\s*(\S+)/) || text.match(/date:\s*(\S+)/i);
    const timestamp = dateMatch
      ? `${dateMatch[1]}T12:00:00Z`
      : new Date().toISOString().replace(/\.\d{3}Z$/, 'Z');
    events.push({
      id: `EVT-${String(seq++).padStart(4, '0')}`,
      type: 'amendment',
      amendment_id: file.replace('.md', ''),
      timestamp,
      summary: `AMENDMENT — ${file}`,
    });
  }
}

events.sort((a, b) => Date.parse(b.timestamp) - Date.parse(a.timestamp));

fs.writeFileSync(outPath, JSON.stringify(events, null, 2) + '\n', 'utf8');
console.log('[GOV-EVENTS] Wrote', path.relative(ROOT, outPath), `(${events.length} event(s))`);
