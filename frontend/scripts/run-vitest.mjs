import { spawn } from 'node:child_process';
import { createRequire } from 'node:module';

const rawArgs = process.argv.slice(2);
const passthroughArgs = [];
let shouldRunOnce = process.env.CI === 'true';
const require = createRequire(import.meta.url);

for (const arg of rawArgs) {
  if (arg === '--run') {
    shouldRunOnce = true;
    continue;
  }

  if (arg === '--watchAll=false' || arg === '--ci' || arg === '--runInBand') {
    shouldRunOnce = true;
    continue;
  }

  if (arg === '--watchAll' || arg === '--watch') {
    continue;
  }

  passthroughArgs.push(arg);
}

const vitestEntry = require.resolve('vitest/vitest.mjs');
const args = [vitestEntry, ...(shouldRunOnce ? ['run'] : []), ...passthroughArgs];

const child = spawn(process.execPath, args, {
  stdio: 'inherit',
  shell: false,
});

child.on('exit', (code, signal) => {
  if (signal) {
    process.kill(process.pid, signal);
    return;
  }

  process.exit(code ?? 1);
});
