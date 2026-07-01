import fs from 'fs';
import path from 'path';
import { ROOT } from './lib/paths.mjs';

const adrDir = path.join(ROOT, 'adr');
const indexPath = path.join(adrDir, 'INDEX.md');

if (!fs.existsSync(adrDir)) {
  console.error('[ADR] adr/ not found');
  process.exit(1);
}

const files = fs
  .readdirSync(adrDir)
  .filter((f) => /^ADR-/.test(f) && f.endsWith('.md'))
  .sort();

const rows = [];
for (const file of files) {
  const text = fs.readFileSync(path.join(adrDir, file), 'utf8');
  const fm = (key) => text.match(new RegExp(`^${key}:\\s*(.+)$`, 'm'))?.[1]?.trim() || '—';
  rows.push({
    id: fm('id'),
    title: fm('title'),
    date: fm('date'),
    doc: fm('doc'),
    status: fm('status'),
    principle: fm('principle'),
    file,
  });
}

let md = `# ADR Index\n\n| ID | Title | Date | Document | Status | Principle |\n|----|-------|------|----------|--------|------------|\n`;
for (const r of rows) {
  md += `| ${r.id} | ${r.title} | ${r.date} | ${r.doc} | ${r.status} | ${r.principle} |\n`;
}
md += `\n_Generated ${new Date().toISOString()}_\n`;

fs.writeFileSync(indexPath, md, 'utf8');
console.log('[ADR] Wrote', path.relative(ROOT, indexPath));
