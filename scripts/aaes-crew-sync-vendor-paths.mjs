#!/usr/bin/env node
/**
 * Sync thin AAES vendor path map from LineageStudio SoT.
 * Does NOT clone Mandala 100 agents.
 */
import { readFileSync, writeFileSync, existsSync } from 'node:fs';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const root = resolve(__dirname, '..');
const lsPaths = resolve(
  'G:/LineageStudio/.cursor/mandala-crew/vendor-skills-paths.json',
);
const aaesMap = resolve(root, '.cursor/aaes-crew/vendor-skills-map.json');
const aaesPaths = resolve(root, '.cursor/aaes-crew/vendor-skills-paths.json');

if (!existsSync(lsPaths)) {
  console.error(`LineageStudio vendor index missing: ${lsPaths}`);
  process.exit(1);
}

const map = JSON.parse(readFileSync(aaesMap, 'utf8'));
const names = new Set();
for (const role of Object.values(map.roles ?? {})) {
  for (const n of role.vendorSkills ?? []) names.add(n);
}

const fallbacks = {
  'check-compiler-errors': [
    'C:/Users/My PC/.cursor/plugins/cache/cursor-public/cursor-team-kit/15ef02d9719259476fbd13de1b2db35d79f04797/skills/check-compiler-errors/SKILL.md',
  ],
};

const source = JSON.parse(readFileSync(lsPaths, 'utf8'));
const paths = {};
const missing = [];
for (const name of [...names].sort()) {
  const entry = source.paths?.[name] ?? fallbacks[name];
  if (entry?.length) paths[name] = entry;
  else missing.push(name);
}

const out = {
  generatedAt: new Date().toISOString(),
  sourceIndex: lsPaths.replace(/\\/g, '/'),
  count: Object.keys(paths).length,
  missing,
  paths,
};

writeFileSync(aaesPaths, `${JSON.stringify(out, null, 2)}\n`, 'utf8');
console.log(
  JSON.stringify(
    { wrote: aaesPaths, count: out.count, missing },
    null,
    2,
  ),
);
if (missing.length) process.exitCode = 0; // soft: keep thin map usable
