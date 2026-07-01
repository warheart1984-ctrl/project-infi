import fs from 'fs';
import path from 'path';
import { ROOT } from './lib/paths.mjs';
import { getDocument } from './lib/version.mjs';

const DOC_ID = process.argv[2] || 'wolf1-arch';
const doc = getDocument(DOC_ID);
const changelogPath = path.join(ROOT, doc.changelog || 'CHANGELOG.md');
const adrDir = path.join(ROOT, 'adr');

if (!fs.existsSync(adrDir)) {
  console.log('[CHANGELOG] No adr/ directory — skipping');
  process.exit(0);
}

const adrs = fs
  .readdirSync(adrDir)
  .filter((f) => /^ADR-/.test(f) && f.endsWith('.md'))
  .sort();

const bullets = [];
for (const file of adrs) {
  const text = fs.readFileSync(path.join(adrDir, file), 'utf8');
  const docTag = text.match(/^doc:\s*(\S+)/m)?.[1];
  if (docTag && docTag !== DOC_ID) continue;

  const title = text.match(/^title:\s*(.+)$/m)?.[1] || file;
  const id = text.match(/^id:\s*(.+)$/m)?.[1] || file.replace('.md', '');
  bullets.push(`- (${id}) ${title}`);
}

if (bullets.length === 0) {
  console.log('[CHANGELOG] No ADRs tagged for', DOC_ID);
  process.exit(0);
}

const version = doc.current_version;
const sectionHeader = `## ${version}`;
let changelog = fs.existsSync(changelogPath)
  ? fs.readFileSync(changelogPath, 'utf8')
  : `# CHANGELOG — ${doc.name}\n\n`;

const adrBlock = `\n### From ADRs\n${bullets.join('\n')}\n`;

if (changelog.includes(sectionHeader)) {
  if (changelog.includes('### From ADRs')) {
    changelog = changelog.replace(
      /### From ADRs[\s\S]*?(?=\n## |\n# |$)/,
      adrBlock.trimEnd() + '\n',
    );
  } else {
    const idx = changelog.indexOf(sectionHeader);
    const nextH2 = changelog.indexOf('\n## ', idx + sectionHeader.length);
    const insertAt = nextH2 === -1 ? changelog.length : nextH2;
    changelog = changelog.slice(0, insertAt) + adrBlock + changelog.slice(insertAt);
  }
} else {
  changelog += `\n${sectionHeader}\n${adrBlock}`;
}

fs.writeFileSync(changelogPath, changelog, 'utf8');
console.log('[CHANGELOG] Updated', path.relative(ROOT, changelogPath));
