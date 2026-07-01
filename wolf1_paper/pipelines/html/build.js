const fs = require('fs');
const path = require('path');

const SRC = path.join(__dirname, '../../src/wolf1_v1.1.md');
const TEMPLATE = path.join(__dirname, 'template.html');
const OUT_HTML = path.join(__dirname, 'wolf1_v1.1.html');
const OUT_PDF = path.join(__dirname, 'wolf1_v1.1.pdf');

function simpleMdToHtml(md) {
  return md
    .replace(/^### (.*)$/gm, '<h3>$1</h3>')
    .replace(/^## (.*)$/gm, '<h2>$1</h2>')
    .replace(/^# (.*)$/gm, '<h1>$1</h1>')
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/^---$/gm, '<hr>')
    .replace(/^\|(.+)\|$/gm, (line) => {
      const cells = line.split('|').filter(Boolean).map((c) => c.trim());
      if (cells.every((c) => /^[-:]+$/.test(c))) return '';
      const tag = line.includes('---') ? 'th' : 'td';
      return `<tr>${cells.map((c) => `<${tag}>${c}</${tag}>`).join('')}</tr>`;
    })
    .split('\n')
    .map((line) => {
      if (line.startsWith('<h') || line.startsWith('<tr') || line.startsWith('<hr')) return line;
      if (!line.trim()) return '';
      return `<p>${line}</p>`;
    })
    .join('\n');
}

(async () => {
  let marked;
  try {
    marked = require('marked');
  } catch {
    marked = null;
  }

  const md = fs.readFileSync(SRC, 'utf8');
  const body = marked ? marked.parse(md) : simpleMdToHtml(md);
  const template = fs.readFileSync(TEMPLATE, 'utf8');
  const html = template.replace('<!-- BODY -->', body);
  fs.writeFileSync(OUT_HTML, html, 'utf8');

  const puppeteer = require('puppeteer');
  const browser = await puppeteer.launch({ headless: 'new' });
  const page = await browser.newPage();
  await page.goto('file://' + OUT_HTML.replace(/\\/g, '/'), { waitUntil: 'networkidle0' });
  await page.pdf({
    path: OUT_PDF,
    format: 'A4',
    printBackground: true,
    margin: { top: '20mm', bottom: '20mm', left: '20mm', right: '20mm' },
  });
  await browser.close();
  console.log('Wrote', OUT_PDF);
})();
