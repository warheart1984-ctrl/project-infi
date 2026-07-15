import { execFileSync } from 'node:child_process';
import { execPath } from 'node:process';
import { describe, expect, it } from 'vitest';

describe('codex handoff orchestrator summary', () => {
  it('includes pricing alongside standards and artifact governance in json mode', () => {
    const output = execFileSync(
      execPath,
      [
        '--import',
        'tsx',
        'tools/codex-handoff-orchestrator.ts',
        'pricing summary check',
        '--next-action',
        'confirm pricing bundle summary payload',
        '--files',
        'docs/crk1/release/SOVEREIGN_ROUTER_X_PRICING.spec.json',
        '--verification',
        'corepack pnpm exec vitest run tests/release/pricing-model.test.ts',
        '--json',
      ],
      { encoding: 'utf8', cwd: process.cwd() },
    );

    const payload = JSON.parse(output) as {
      ok: boolean;
      pricing: { pricingScenarioMatrix: unknown[] };
      pricingSummary: { scenarioCount: number };
      standards: unknown;
      artifactGovernance: unknown;
      externalStandards: unknown;
    };

    expect(payload.ok).toBe(true);
    expect(payload.standards).toBeDefined();
    expect(payload.artifactGovernance).toBeDefined();
    expect(payload.externalStandards).toBeDefined();
    expect(payload.pricing).toBeDefined();
    expect(payload.pricing.pricingScenarioMatrix).toHaveLength(payload.pricingSummary.scenarioCount);
    expect(payload.pricingSummary.scenarioCount).toBeGreaterThanOrEqual(5);
  }, 30000);
});
