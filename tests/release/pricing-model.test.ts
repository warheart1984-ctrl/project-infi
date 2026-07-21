import { describe, expect, it } from 'vitest';
import { loadPricingModelSpec, summarizePricingModelSpec } from '../../tools/pricing-model.js';

describe('sovereign router x pricing model', () => {
  it('loads the layered pricing spec', () => {
    const spec = loadPricingModelSpec();

    expect(spec.revenueLayers.map((layer) => layer.name)).toContain('Governance & Assurance');
    expect(spec.customerSegments.map((segment) => segment.name)).toContain('Public Sector');
    expect(spec.pricingStrategies).toContain('Enterprise bundle');
    expect(spec.pricingScenarioMatrix).toHaveLength(spec.customerSegments.length);
    expect(spec.pricingScenarioMatrix[0]?.models.map((model) => model.strategy)).toContain('Subscription-led');
  });

  it('summarizes the layer and segment counts', () => {
    const summary = summarizePricingModelSpec();

    expect(summary.revenueLayerCount).toBeGreaterThanOrEqual(6);
    expect(summary.customerSegmentCount).toBeGreaterThanOrEqual(5);
    expect(summary.strategyCount).toBeGreaterThan(0);
    expect(summary.scenarioCount).toBeGreaterThanOrEqual(5);
  });
});
