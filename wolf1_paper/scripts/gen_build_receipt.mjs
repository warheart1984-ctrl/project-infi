import fs from 'fs';
import path from 'path';
import crypto from 'crypto';
import { spawnSync } from 'child_process';
import { ROOT } from './lib/paths.mjs';
import { getDocument } from './lib/version.mjs';
import { collectTraceability } from './collect_traceability.mjs';

const DOC_ID = process.argv[2] || 'wolf1-arch';
const BUILD_DIR = process.argv[3] || 'build';

const doc = getDocument(DOC_ID);
const version = doc.current_version;
const srcPath = path.join(ROOT, doc.source);
const buildPath = path.join(ROOT, BUILD_DIR);
const receiptsDir = path.join(ROOT, 'governance', 'receipts');
fs.mkdirSync(receiptsDir, { recursive: true });

const basename = path.basename(doc.source, '.md');
const pdfName = `${basename}-${version}.pdf`;
const htmlName = `${basename}-${version}.html`;
const pdfPath = path.join(buildPath, pdfName);
const htmlPath = path.join(buildPath, htmlName);

if (!fs.existsSync(pdfPath) || !fs.existsSync(htmlPath)) {
  console.error('[RECEIPT][FAIL] Missing build outputs. Run: npm run build:pdf');
  process.exit(1);
}

const sha = (file) =>
  crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex');

let commit = 'unknown';
const git = spawnSync('git', ['rev-parse', 'HEAD'], { cwd: ROOT, encoding: 'utf8' });
if (git.status === 0) commit = git.stdout.trim();

const ctsRun = spawnSync(process.execPath, ['cts/run_all.mjs'], { cwd: ROOT });
const ctsStatus = ctsRun.status === 0 ? 'PASS' : 'FAIL';

const timestamp = new Date().toISOString().replace(/\.\d{3}Z$/, 'Z');
const fileStamp = timestamp.replace(/:/g, '-');
const receiptFile = path.join(receiptsDir, `${DOC_ID}-${version}-${fileStamp}.json`);

const pdfSha = sha(pdfPath);
const htmlSha = sha(htmlPath);

const receipt = {
  receipt_id: `REC-${DOC_ID}-${version}`,
  document_id: DOC_ID,
  version,
  timestamp,
  commit,
  source: doc.source,
  source_sha256: sha(srcPath),
  artifacts: {
    pdf_sha256: pdfSha,
    html_sha256: htmlSha,
    pdf_file: pdfName,
    html_file: htmlName,
  },
  outputs: {
    pdf: { file: pdfName, path: `${BUILD_DIR}/${pdfName}`, sha256: pdfSha },
    html: { file: htmlName, path: `${BUILD_DIR}/${htmlName}`, sha256: htmlSha },
  },
  cts_status: ctsStatus,
  cts_passed: ctsStatus === 'PASS',
  traceability: collectTraceability(),
  builder: process.env.BUILDER || 'cursor',
};

fs.writeFileSync(receiptFile, JSON.stringify(receipt, null, 2) + '\n', 'utf8');
console.log('[RECEIPT] Created:', path.relative(ROOT, receiptFile));

const idx = spawnSync(process.execPath, ['scripts/gen_dashboard_artifacts.mjs'], {
  cwd: ROOT,
  stdio: 'inherit',
});
if (idx.status !== 0) process.exit(idx.status ?? 1);
