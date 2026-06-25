#!/usr/bin/env node
/**
 * Drift demo — runs 15 noisy UCR sessions and prints drift + top patterns.
 *
 * Usage (from aaes-os/):
 *   pnpm drift-demo
 */
import {
  DriftMetrics,
  initGovernanceGlobals,
} from '@aaes-os/aaes-governance';
import { TraceBus } from '@aaes-os/trace-bus';
import { UCRRuntime } from '@aaes-os/ucr-runtime';

const BATCH_SIZE = 15;

async function main(): Promise<void> {
  const { journal, patterns: patternLedger } = initGovernanceGlobals();
  const traceBus = new TraceBus();

  const runtime = new UCRRuntime({
    traceBus,
    faultJournal: journal,
    enablePatches: false,
    demoSchedule: ['good', 'string', 'random'],
  });

  console.log(`\n=== AAES-OS Drift Demo (${BATCH_SIZE} runs) ===\n`);

  for (let batch = 1; batch <= 3; batch += 1) {
    const runsInBatch = Math.ceil(BATCH_SIZE / 3);
    for (let i = 0; i < runsInBatch; i += 1) {
      await runtime.run({
        kind: 'drift-demo',
        payload: { batch, index: i },
      });
    }

    const drift = new DriftMetrics().computeDrift(journal.getAll(), patternLedger.getAll());

    console.log(`--- After batch ${batch} ---`);
    console.log(`Drift score: ${drift.score} (faults=${drift.totalFaults}, patterns=${drift.uniquePatterns})`);
    console.log('Top patterns:');
    for (const pattern of patternLedger.getTopRecurring(5)) {
      console.log(`  ${pattern.patternId} → recurrence ${pattern.recurrence}`);
    }
    console.log('');
  }
}

main().catch((error: unknown) => {
  console.error(error);
  process.exitCode = 1;
});
