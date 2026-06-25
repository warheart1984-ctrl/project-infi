#!/usr/bin/env node

/**
 * AAES-OS Release Notes Generator
 * Generates RELEASE_NOTES.md from dashboard, ledger, backlog, and git history.
 */

import fs from 'node:fs';
import path from 'node:path';
import { execSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const aaesRoot = path.resolve(__dirname, '..');

function read(file) {
  const p = path.join(aaesRoot, file);
  return fs.existsSync(p) ? fs.readFileSync(p, 'utf8') : '';
}

function section(title, body) {
  return `## ${title}\n\n${body.trim()}\n\n`;
}

function sliceBetween(text, start, end) {
  const i = text.indexOf(start);
  if (i < 0) return '';
  const j = text.indexOf(end, i + start.length);
  return j < 0 ? text.slice(i + start.length).trim() : text.slice(i + start.length, j).trim();
}

function generate() {
  const dashboard = read('RELEASE_DASHBOARD.md');
  const deliverables = sliceBetween(dashboard, '## 1. Deliverables', '## 2. Release Gates');
  const gates = sliceBetween(dashboard, '## 2. Release Gates', '## 3. Evidence Status');
  const evidence = sliceBetween(read('EVIDENCE_LEDGER.md'), '## Evidence Ledger', '## How to Update');
  const backlog = read('VERSION_2_BACKLOG.md').trim();

  let commits = '';
  try {
    commits = execSync("git log --pretty=format:'- %s' --no-merges -n 50", {
      cwd: aaesRoot,
      encoding: 'utf8',
    });
  } catch {
    commits = '- (git history unavailable)';
  }

  const notes = `# AAES-OS v1.0 Release Notes

${section(
  'Overview',
  `AAES-OS v1.0 is the first governed, deterministic runtime spine for agentic systems.
This release includes CAS 1.0, CRK-1, CTS, CEP, CDP-1 scaffolding, and the full documentation suite.`,
)}

${section('Deliverables', deliverables)}

${section('Release Gates', gates)}

${section('Evidence Summary', evidence)}

${section('Recent Changes', commits)}

${section('Version 2.0 Backlog', backlog)}

---

Generated automatically by \`scripts/generate-release-notes.js\`.
`;

  const out = path.join(aaesRoot, 'RELEASE_NOTES.md');
  fs.writeFileSync(out, notes);
  console.log('Release notes generated:', out);
}

generate();
