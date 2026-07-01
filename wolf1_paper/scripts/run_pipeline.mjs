import { spawnSync } from 'child_process';
import { ROOT } from './lib/paths.mjs';

const target = process.argv[2] || 'all';
const steps = {
  sync: ['node', 'src/sync_sections_from_master.js'],
  enforce: ['bash', 'scripts/enforce_governance.sh'],
  traceability: ['node', 'scripts/validate_traceability_chain.mjs'],
  cts: ['node', 'cts/run_all.mjs'],
  pdf: ['node', 'build.mjs', 'wolf1-arch', '--skip-cts'],
  changelog: ['node', 'scripts/update_changelog.mjs'],
  amendments: ['node', 'scripts/gen_amendment_diffs.mjs'],
  receipt: ['node', 'scripts/gen_build_receipt.mjs'],
  'receipt-index': ['node', 'scripts/gen_dashboard_artifacts.mjs'],
  dashboard: ['node', 'scripts/gen_dashboard_artifacts.mjs'],
  'adr-index': ['node', 'scripts/gen_adr_index.mjs'],
  diagrams: ['node', 'scripts/gen_diagrams_from_specs.mjs'],
};

const order =
  target === 'all'
    ? ['enforce', 'cts', 'pdf', 'changelog', 'amendments', 'receipt', 'receipt-index', 'adr-index', 'diagrams']
    : [target];

for (const step of order) {
  const cmd = steps[step];
  if (!cmd) {
    console.error('Unknown step:', step);
    process.exit(1);
  }
  console.log(`\n[PIPELINE] >>> ${step}`);
  const r = spawnSync(cmd[0], cmd.slice(1), { cwd: ROOT, stdio: 'inherit', shell: false });
  if (r.status !== 0) process.exit(r.status ?? 1);
}

console.log('\n[PIPELINE] Complete');
