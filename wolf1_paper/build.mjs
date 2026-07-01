import fs from 'fs';
import path from 'path';
import { spawnSync } from 'child_process';
import { ROOT } from './scripts/lib/paths.mjs';
import { getDocument, resolveFromRoot } from './scripts/lib/version.mjs';

const args = process.argv.slice(2).filter((a) => !a.startsWith('--'));
const DOC_ID = process.env.DOC_ID || args[0] || 'wolf1-arch';
const SKIP_CTS = process.argv.includes('--skip-cts');

function hasCommand(cmd) {
  const r = spawnSync(cmd, ['--version'], { shell: true, stdio: 'pipe' });
  return r.status === 0;
}

async function runCts() {
  const r = spawnSync(process.execPath, ['cts/run_all.mjs'], {
    cwd: ROOT,
    stdio: 'inherit',
  });
  if (r.status !== 0) process.exit(r.status ?? 1);
}

async function buildWithPandoc(src, pdfOut, htmlOut) {
  const pandoc = spawnSync(
    'pandoc',
    [src, '--from', 'markdown', '--to', 'pdf', '--output', pdfOut],
    { cwd: ROOT, stdio: 'inherit' },
  );
  if (pandoc.status !== 0) throw new Error('pandoc PDF failed');

  spawnSync(
    'pandoc',
    [src, '--from', 'markdown', '--to', 'html', '--standalone', '--output', htmlOut],
    { cwd: ROOT, stdio: 'inherit' },
  );
}

function findSystemBrowser() {
  if (process.env.PUPPETEER_EXECUTABLE_PATH && fs.existsSync(process.env.PUPPETEER_EXECUTABLE_PATH)) {
    return process.env.PUPPETEER_EXECUTABLE_PATH;
  }
  const local = process.env.LOCALAPPDATA || '';
  const candidates = [
    path.join(local, 'Google', 'Chrome', 'Application', 'chrome.exe'),
    'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
    'C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe',
    path.join(local, 'Microsoft', 'Edge', 'Application', 'msedge.exe'),
    'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe',
  ];
  return candidates.find((p) => fs.existsSync(p));
}

async function buildWithPuppeteer(src, pdfOut, htmlOut) {
  const { marked } = await import('marked');
  const puppeteer = await import('puppeteer');

  const md = fs.readFileSync(src, 'utf8');
  const body = marked.parse(md);
  const templatePath = path.join(ROOT, 'pipelines/html/template.html');
  let html = fs.readFileSync(templatePath, 'utf8');
  html = html.replace('<!-- BODY -->', body);
  fs.writeFileSync(htmlOut, html, 'utf8');

  const launchOpts = { headless: true };
  const systemBrowser = findSystemBrowser();
  if (systemBrowser) {
    launchOpts.executablePath = systemBrowser;
    console.log('[BUILD] Using system browser:', systemBrowser);
  }

  const browser = await puppeteer.default.launch(launchOpts);
  const page = await browser.newPage();
  const fileUrl = 'file:///' + htmlOut.replace(/\\/g, '/');
  await page.goto(fileUrl, { waitUntil: 'networkidle0' });
  await page.pdf({
    path: pdfOut,
    format: 'A4',
    printBackground: true,
    margin: { top: '20mm', bottom: '20mm', left: '20mm', right: '20mm' },
  });
  await browser.close();
}

async function main() {
  const doc = getDocument(DOC_ID);
  const version = doc.current_version;
  const src = resolveFromRoot(doc.source);
  const buildDir = resolveFromRoot('build');
  const basename = path.basename(doc.source, '.md');

  if (!fs.existsSync(src)) {
    console.error(`[BUILD] Source not found: ${src}`);
    process.exit(1);
  }

  fs.mkdirSync(buildDir, { recursive: true });

  const versionedPdf = path.join(buildDir, `${basename}-${version}.pdf`);
  const versionedHtml = path.join(buildDir, `${basename}-${version}.html`);
  const aliasPdf = path.join(buildDir, `${basename}.pdf`);

  console.log(`[BUILD] Document: ${DOC_ID}`);
  console.log(`[BUILD] Version:  ${version}`);
  console.log(`[BUILD] Source:   ${doc.source}`);

  if (!SKIP_CTS) {
    console.log('[BUILD] Running CTS gate...');
    await runCts();
  }

  if (hasCommand('pandoc')) {
    console.log('[BUILD] Using pandoc');
    await buildWithPandoc(src, versionedPdf, versionedHtml);
  } else {
    console.log('[BUILD] pandoc not found — using puppeteer fallback');
    await buildWithPuppeteer(src, versionedPdf, versionedHtml);
  }

  fs.copyFileSync(versionedPdf, aliasPdf);

  console.log('[BUILD] Outputs:');
  console.log(`  - ${path.relative(ROOT, versionedPdf)}`);
  console.log(`  - ${path.relative(ROOT, versionedHtml)}`);
  console.log(`  - ${path.relative(ROOT, aliasPdf)} (alias)`);
}

main().catch((err) => {
  console.error('[BUILD] Failed:', err.message);
  process.exit(1);
});
