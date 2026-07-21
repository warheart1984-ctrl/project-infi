import { describe, expect, it } from 'vitest';

import { SovereignXRouter } from './SovereignXRouter.js';
import {
  createPricingLedgerEntry,
  evaluateSovereignRouterXPricing,
  listSovereignRouterXPricingScenarioMatrix,
  normalizeSovereignRouterXPricingInput,
} from './pricing.js';

describe('Sovereign Router X pricing', () => {
  it('normalizes pricing input and evaluates a recommended commercial plan', () => {
    const input = normalizeSovereignRouterXPricingInput({
      segment: 'Enterprise',
      monthlyCustomers: 12,
      routedRequestsPerCustomer: 340,
      governanceReviewsPerCustomer: 7,
      knowledgeUpdatesPerCustomer: 9,
      serviceHoursPerCustomer: 3,
      compliancePressure: 86,
      workloadVolatility: 48,
      supportComplexity: 81,
      privateDeployment: true,
      assuranceRequired: true,
    });

    const evaluation = evaluateSovereignRouterXPricing(input, { router: new SovereignXRouter(), requestId: 'pricing-test' });

    expect(evaluation.input.segment).toBe('Enterprise');
    expect(evaluation.strategyScenarios).toHaveLength(4);
    expect(evaluation.recommendedScenario.strategy).toBe('Enterprise bundle');
    expect(evaluation.recommendedScenario.estimatedGrossMarginPct).toBeGreaterThan(0);
    expect(evaluation.routing.modelDecision.model).toBe('qwen-7b');
    expect(evaluation.requestPacket.objective).toContain('Sovereign Router X pricing');
    expect(evaluation.ledgerEntry.requestId).toBe('pricing-test');
    expect(evaluation.ledgerEntry.strategy).toBe('Enterprise bundle');
    expect(evaluation.economics.monthlyRevenueUsd).toBeGreaterThan(evaluation.economics.monthlyDirectCostUsd);
  });

  it('publishes a companion scenario matrix for every segment', () => {
    const matrix = listSovereignRouterXPricingScenarioMatrix();

    expect(matrix).toHaveLength(5);
    expect(matrix.map((row) => row.segment)).toEqual([
      'Individual',
      'Professional',
      'Team',
      'Enterprise',
      'Public Sector',
    ]);
    expect(matrix.every((row) => row.models.length === 4)).toBe(true);
  });

  it('creates a ledger entry from an evaluation without mutating the result', () => {
    const evaluation = evaluateSovereignRouterXPricing({
      segment: 'Professional',
      monthlyCustomers: 3,
      routedRequestsPerCustomer: 90,
      governanceReviewsPerCustomer: 2,
      knowledgeUpdatesPerCustomer: 4,
      serviceHoursPerCustomer: 1,
      compliancePressure: 42,
      workloadVolatility: 33,
      supportComplexity: 28,
      privateDeployment: false,
      assuranceRequired: false,
    }, { router: new SovereignXRouter() });

    const entry = createPricingLedgerEntry(evaluation);

    expect(entry.segment).toBe('Professional');
    expect(entry.requestId).toMatch(/^srx-/);
    expect(entry.estimatedGrossMarginUsd).toBeCloseTo(evaluation.economics.grossMarginUsd, 6);
  });
});

