import fs from 'fs';
import path from 'path';
import { spawnSync } from 'child_process';
import { ROOT } from './lib/paths.mjs';

const amendmentsDir = path.join(ROOT, 'amendments');
const buildDir = path.join(ROOT, 'build');
fs.mkdirSync(buildDir, { recursive: true });

if (!fs.existsSync(amendmentsDir)) {
  console.log('[AMENDMENTS] No amendments/ directory');
  process.exit(0);
}

const files = fs
  .readdirSync(amendmentsDir)
  .filter((f) => f.endsWith('.md'))
  .sort();

if (files.length < 2) {
  console.log('[AMENDMENTS] Single amendment file — writing summary only');
  if (files.length === 1) {
    const out = path.join(buildDir, 'amendment-latest.md');
    fs.copyFileSync(path.join(amendmentsDir, files[0]), out);
    console.log('[AMENDMENTS] Wrote', path.relative(ROOT, out));
  }
  process.exit(0);
}

for (let i = 0; i < files.length - 1; i++) {
  const a = path.join(amendmentsDir, files[i]);
  const b = path.join(amendmentsDir, files[i + 1]);
  const base = files[i].replace('.md', '') + '_' + files[i + 1].replace('.md', '');
  const out = path.join(buildDir, `amendment-${base}.diff.md`);

  const r = spawnSync('git', ['diff', '--no-index', a, b], {
    encoding: 'utf8',
    shell: true,
  });

  const diffBody = r.stdout || r.stderr || '(no diff output)';
  const md = `# Amendment diff: ${files[i]} → ${files[i + 1]}\n\n\`\`\`diff\n${diffBody}\n\`\`\`\n`;
  fs.writeFileSync(out, md, 'utf8');
  console.log('[AMENDMENTS] Wrote', path.relative(ROOT, out));
}
