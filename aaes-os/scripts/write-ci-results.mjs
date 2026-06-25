#!/usr/bin/env node

/**
 * Runs aaes-os test scripts and writes CI gatekeeper JSON artifacts.
 */

import fs from 'node:fs';
import path from 'node:path';
import { execSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const aaesRoot = path.resolve(__dirname, '..');
const ciDir = path.join(aaesRoot, '.ci');

fs.mkdirSync(ciDir, { recursive: true });

function run(cmd) {
  execSync(cmd, { cwd: aaesRoot, stdio: 'inherit', shell: true });
}

let ctsOk = false;
let detOk = false;
let govOk = false;

try {
  run('pnpm exec vitest run tests/integration benchmarks/cdp1');
  ctsOk = true;
} catch {
  ctsOk = false;
}

try {
  run('pnpm exec tsx tools/validateDeterministicReplay.ts');
  detOk = true;
} catch {
  detOk = false;
}

try {
  run('pnpm exec vitest run packages/aaes-governance');
  govOk = true;
} catch {
  govOk = false;
}

fs.writeFileSync(
  path.join(ciDir, 'cts_results.json'),
  JSON.stringify({ allPassed: ctsOk, timestamp: new Date().toISOString() }, null, 2),
);
fs.writeFileSync(
  path.join(ciDir, 'determinism_results.json'),
  JSON.stringify({ deterministic: detOk, timestamp: new Date().toISOString() }, null, 2),
);
fs.writeFileSync(
  path.join(ciDir, 'governance_results.json'),
  JSON.stringify({ allPassed: govOk, timestamp: new Date().toISOString() }, null, 2),
);

console.log('CI results written to', ciDir);
if (!ctsOk || !detOk || !govOk) {
  process.exit(1);
}
