import { describe, expect, it } from 'vitest';

import { createReleaseReceipt } from '../../release/receipt.ts';

function manifestFixture() {
  return {
    name: 'aaes-os',
    version: '0.2.0-test',
    bundle: 'release/bundle',
    artifacts: ['release/release-manifest.json'],
  };
}

function checksumsFixture() {
  return {
    files: [
      {
        path: 'release/release-manifest.json',
        sha256: '0'.repeat(64),
        size: 10,
      },
    ],
  };
}

describe('release receipt evidence', () => {
  it('does not bake stale hardcoded test counts or verification dates', () => {
    const receipt = createReleaseReceipt(manifestFixture(), checksumsFixture(), {
      generatedAt: '2026-08-02T00:00:00.000Z',
    });

    const serialized = JSON.stringify(receipt);
    expect(serialized).not.toContain('435 passed');
    expect(serialized).not.toContain('2026-07-14');
    expect(serialized).not.toContain('579');
    expect(serialized).not.toContain('149 passed');

    const notes = [
      ...receipt.testEvidence.notes,
      ...receipt.lintStatus.notes,
      ...receipt.replayStatus.notes,
    ].join('\n');
    expect(notes).not.toMatch(/2026-07-\d\d/);
  });

  it('accepts explicit test evidence via extras', () => {
    const receipt = createReleaseReceipt(manifestFixture(), checksumsFixture(), {
      generatedAt: '2026-08-02T00:00:00.000Z',
      testEvidence: {
        status: 'Observed',
        evidence: ['pnpm exec vitest run (151 passed files, 589 passed tests, 2 skipped)'],
        notes: ['Fresh local verification completed on 2026-08-02.'],
      },
    });

    expect(receipt.testEvidence.evidence[0]).toContain('589 passed tests');
    expect(receipt.testEvidence.notes[0]).toContain('2026-08-02');
    expect(receipt.lintStatus.notes[0]).not.toMatch(/2026-07-\d\d/);
  });

  it('derives the fresh verification note from the generatedAt timestamp', () => {
    const receipt = createReleaseReceipt(manifestFixture(), checksumsFixture(), {
      generatedAt: '2026-08-02T01:12:22.067Z',
    });

    expect(receipt.testEvidence.notes[0]).toContain('2026-08-02T01:12:22.067Z');
  });
});
