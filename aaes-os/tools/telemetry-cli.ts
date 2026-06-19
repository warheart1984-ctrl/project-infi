#!/usr/bin/env node
/**
 * Telemetry CLI — prints drift score, top patterns, and recent faults.
 *
 * Usage (from aaes-os/):
 *   pnpm telemetry
 *   pnpm telemetry --seed
 */
import {
  collectTelemetrySnapshot,
  initGovernanceGlobals,
} from '@aaes-os/aaes-governance';
import { UCRRuntime } from '@aaes-os/ucr-runtime';

const SEED_RUNS = 10;

async function maybeSeed(): Promise<void> {
  if (!process.argv.includes('--seed')) {
    return;
  }

  const runtime = new UCRRuntime({
    enablePatches: false,
    demoSchedule: ['good', 'string', 'random'],
  });
  for (let i = 0; i < SEED_RUNS; i += 1) {
    await runtime.run({
      kind: 'telemetry-seed',
      payload: { index: i },
    });
  }
}

function printSnapshot(): void {
  const { drift, topPatterns, lastFaults } = collectTelemetrySnapshot(10);

  console.log('\n=== AAES-OS Telemetry ===\n');
  console.log(`DRIFT SCORE: ${drift.score} (faults=${drift.totalFaults}, patterns=${drift.uniquePatterns})`);
  console.log('\nTOP PATTERNS (5):');
  if (topPatterns.length === 0) {
    console.log('  (none)');
  } else {
    for (const pattern of topPatterns) {
      console.log(`  ${pattern.patternId} → recurrence ${pattern.recurrence}`);
    }
  }

  console.log('\nLAST 10 FAULTS:');
  if (lastFaults.length === 0) {
    console.log('  (none)');
  } else {
    for (const fault of lastFaults) {
      console.log(
        `  ${fault.timestamp} ${fault.faultCode} run=${fault.runId} severity=${fault.severity}`,
      );
    }
  }
  console.log('');
}

async function main(): Promise<void> {
  initGovernanceGlobals();
  await maybeSeed();
  printSnapshot();
}

main().catch((error: unknown) => {
  console.error(error);
  process.exitCode = 1;
});
