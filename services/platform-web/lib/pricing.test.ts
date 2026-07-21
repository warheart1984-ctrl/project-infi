import { describe, expect, it } from 'vitest';

import { buildPricingLedgerEntry, evaluatePublicPricing, DEFAULT_PRICING_INPUT } from './pricing';

describe('public pricing evaluator', () => {
  it('routes the pricing request and returns ledger-ready economics', () => {
    const evaluation = evaluatePublicPricing({
      ...DEFAULT_PRICING_INPUT,
      segment: 'Public Sector',
      monthlyCustomers: 9,
      routedRequestsPerCustomer: 420,
      governanceReviewsPerCustomer: 6,
      knowledgeUpdatesPerCustomer: 8,
      serviceHoursPerCustomer: 2,
      compliancePressure: 88,
      workloadVolatility: 39,
      supportComplexity: 84,
      privateDeployment: true,
      assuranceRequired: true,
    }, 'public-pricing-enterprise');

    const ledgerEntry = buildPricingLedgerEntry(evaluation);

    expect(evaluation.recommendedScenario.strategy).toBe('Enterprise bundle');
    expect(evaluation.routing.modelDecision.model).toBe('qwen-7b');
    expect(evaluation.economics.monthlyRevenueUsd).toBeGreaterThan(evaluation.economics.monthlyDirectCostUsd);
    expect(evaluation.requestPacket.objective).toContain('Sovereign Router X pricing');
    expect(ledgerEntry.strategy).toBe('Enterprise bundle');
    expect(ledgerEntry.requestId).toBe('public-pricing-enterprise');
  });

  it('keeps the lightweight evaluator deterministic for small public workloads', () => {
    const evaluation = evaluatePublicPricing({
      ...DEFAULT_PRICING_INPUT,
      segment: 'Individual',
      monthlyCustomers: 1,
      routedRequestsPerCustomer: 30,
      governanceReviewsPerCustomer: 0,
      knowledgeUpdatesPerCustomer: 1,
      serviceHoursPerCustomer: 0,
      compliancePressure: 8,
      workloadVolatility: 18,
      supportComplexity: 12,
      privateDeployment: false,
      assuranceRequired: false,
    }, 'public-pricing-test');

    expect(evaluation.requestPacket.blockers).toHaveLength(0);
    expect(evaluation.routing.routeEvaluation.workItem.intentId).toBe('sovereign-router-x-pricing');
    expect(evaluation.strategyScenarios[0].strategy).toBeDefined();
  });
});
