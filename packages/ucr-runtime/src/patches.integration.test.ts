import { describe, expect, it } from 'vitest';

import {
  countInvariantFaults,
  countSpanBoundaryFaults,
} from '@aaes-os/aaes-governance';
import { UCRRuntime, type DemoRunMode } from '@aaes-os/ucr-runtime';

const DEMO_SCHEDULE: DemoRunMode[] = [
  ...Array.from<DemoRunMode>({ length: 12 }).fill('string'),
  ...Array.from<DemoRunMode>({ length: 8 }).fill('random'),
];

describe('governance patches integration', () => {
  it('reduces invariant faults when patches are enabled', async () => {
    const withoutPatches = new UCRRuntime({ enablePatches: false, demoSchedule: DEMO_SCHEDULE });
    const withPatches = new UCRRuntime({ enablePatches: true, demoSchedule: DEMO_SCHEDULE });

    const preResults = [];
    const postResults = [];

    for (let index = 0; index < 20; index += 1) {
      preResults.push(await withoutPatches.run({ kind: 'demo', runIndex: index }));
      postResults.push(await withPatches.run({ kind: 'demo', runIndex: index }));
    }

    const preShape = countInvariantFaults(
      preResults.flatMap((result) => result.faults),
      'INV_OUTPUT_SHAPE',
    );
    const postShape = countInvariantFaults(
      postResults.flatMap((result) => result.faults),
      'INV_OUTPUT_SHAPE',
    );
    const preDeterminism = countInvariantFaults(
      preResults.flatMap((result) => result.faults),
      'INV_DETERMINISM',
    );
    const postDeterminism = countInvariantFaults(
      postResults.flatMap((result) => result.faults),
      'INV_DETERMINISM',
    );

    expect(preShape).toBe(12);
    expect(postShape).toBe(0);
    expect(preDeterminism).toBe(8);
    expect(postDeterminism).toBe(0);
    expect(postDeterminism).toBeLessThan(preDeterminism);
    expect(postShape).toBeLessThan(preShape);
  });

  it('withSpanGuard prevents span orphan faults on thrown executePlan', async () => {
    const throwSchedule: DemoRunMode[] = ['throw', 'throw', 'throw'];
    const withoutPatches = new UCRRuntime({ enablePatches: false, demoSchedule: throwSchedule });
    const withPatches = new UCRRuntime({ enablePatches: true, demoSchedule: throwSchedule });

    const pre = [];
    const post = [];
    for (let index = 0; index < 3; index += 1) {
      pre.push(await withoutPatches.run({ kind: 'span-demo', runIndex: index }));
      post.push(await withPatches.run({ kind: 'span-demo', runIndex: index }));
    }

    expect(countSpanBoundaryFaults(pre.flatMap((result) => result.faults))).toBe(3);
    expect(countSpanBoundaryFaults(post.flatMap((result) => result.faults))).toBe(0);
  });
});
