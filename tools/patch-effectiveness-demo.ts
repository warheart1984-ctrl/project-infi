#!/usr/bin/env node
/**
 * Patch effectiveness demo — compares fault recurrence with patches off vs on.
 * Run: pnpm patch-demo
 */
import {
  PatchAnalytics,
  countInvariantFaults,
  countSpanBoundaryFaults,
  type FaultEvent,
} from '@aaes-os/aaes-governance';
import { registerSamplePatchProposals } from '@aaes-os/tri-core-protocol';
import { UCRRuntime, type DemoRunMode } from '@aaes-os/ucr-runtime';

const INVARIANT_SCHEDULE: DemoRunMode[] = [
  ...Array.from<DemoRunMode>({ length: 12 }).fill('string'),
  ...Array.from<DemoRunMode>({ length: 8 }).fill('random'),
];

const SPAN_SCHEDULE: DemoRunMode[] = ['throw', 'throw', 'throw'];

async function runSchedule(
  enablePatches: boolean,
  schedule: DemoRunMode[],
  label: string,
): Promise<FaultEvent[]> {
  const runtime = new UCRRuntime({ enablePatches, demoSchedule: schedule });
  const faults: FaultEvent[] = [];

  for (let index = 0; index < schedule.length; index += 1) {
    const result = await runtime.run({ kind: label, runIndex: index });
    faults.push(...result.faults);
  }

  return faults;
}

async function main(): Promise<void> {
  const proposals = registerSamplePatchProposals();
  console.log('Tri-Core patch proposals (DEPLOYED):');
  for (const proposal of proposals) {
    console.log(`  - ${proposal.patchId}: ${proposal.description}`);
  }
  console.log('');

  const analytics = new PatchAnalytics();

  const preInvariantFaults = await runSchedule(false, INVARIANT_SCHEDULE, 'pre-invariant');
  const preSpanFaults = await runSchedule(false, SPAN_SCHEDULE, 'pre-span');
  const postInvariantFaults = await runSchedule(true, INVARIANT_SCHEDULE, 'post-invariant');
  const postSpanFaults = await runSchedule(true, SPAN_SCHEDULE, 'post-span');

  const preShape = countInvariantFaults(preInvariantFaults, 'INV_OUTPUT_SHAPE');
  const postShape = countInvariantFaults(postInvariantFaults, 'INV_OUTPUT_SHAPE');
  const preDeterminism = countInvariantFaults(preInvariantFaults, 'INV_DETERMINISM');
  const postDeterminism = countInvariantFaults(postInvariantFaults, 'INV_DETERMINISM');
  const preSpan = countSpanBoundaryFaults(preSpanFaults);
  const postSpan = countSpanBoundaryFaults(postSpanFaults);

  analytics.recordEffectiveness('PATCH_OUTPUT_SHAPE_001', preShape, postShape);
  analytics.recordEffectiveness('PATCH_DETERMINISM_001', preDeterminism, postDeterminism);
  analytics.recordEffectiveness('PATCH_SPAN_BOUNDARY_001', preSpan, postSpan);

  console.log('Patch effectiveness timeline:');
  for (const record of analytics.getTimeline()) {
    console.log(
      `  ${record.patchId}: pre=${record.preRecurrence} post=${record.postRecurrence} effectiveness=${record.effectiveness}`,
    );
  }
}

main().catch((error: unknown) => {
  console.error(error);
  process.exit(1);
});
