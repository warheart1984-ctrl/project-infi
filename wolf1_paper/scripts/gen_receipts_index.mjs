import fs from 'fs';
import path from 'path';
import { ROOT } from './lib/paths.mjs';

const receiptsDir = path.join(ROOT, 'governance', 'receipts');
const indexPath = path.join(ROOT, 'governance', 'receipts-index.json');

fs.mkdirSync(receiptsDir, { recursive: true });

const files = fs.existsSync(receiptsDir)
  ? fs
      .readdirSync(receiptsDir)
      .filter((f) => f.endsWith('.json') && f !== 'receipts-index.json')
  : [];

const receipts = [];
for (const file of files) {
  try {
    const data = JSON.parse(fs.readFileSync(path.join(receiptsDir, file), 'utf8'));
    receipts.push({
      ...data,
      _file: file,
    });
  } catch (err) {
    console.warn('[RECEIPTS-INDEX] skip invalid JSON:', file, err.message);
  }
}

receipts.sort((a, b) => {
  const ta = Date.parse(a.timestamp || 0);
  const tb = Date.parse(b.timestamp || 0);
  return tb - ta;
});

const index = receipts.map(({ _file, ...rest }) => rest);
fs.writeFileSync(indexPath, JSON.stringify(index, null, 2) + '\n', 'utf8');
console.log('[RECEIPTS-INDEX] Wrote', path.relative(ROOT, indexPath), `(${index.length} receipt(s))`);
