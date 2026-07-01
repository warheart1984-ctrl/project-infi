import { spawnSync } from 'child_process';
import { ROOT } from './lib/paths.mjs';

const steps = [
  ['gen_receipts_index.mjs'],
  ['gen_governance_status.mjs'],
  ['gen_governance_events.mjs'],
];

for (const args of steps) {
  const r = spawnSync(process.execPath, ['scripts/' + args[0]], {
    cwd: ROOT,
    stdio: 'inherit',
  });
  if (r.status !== 0) process.exit(r.status ?? 1);
}

console.log('[DASHBOARD] Artifacts refreshed');
