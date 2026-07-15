import {
  createPricingLedgerEntry,
  evaluateSovereignRouterXPricing,
  normalizeSovereignRouterXPricingInput,
  type SovereignRouterXPricingEvaluation,
  type SovereignRouterXPricingInput,
} from '@aaes-os/sovereignx-router';

export const DEFAULT_PRICING_INPUT: SovereignRouterXPricingInput = normalizeSovereignRouterXPricingInput({
  segment: 'Professional',
  monthlyCustomers: 1,
  routedRequestsPerCustomer: 120,
  governanceReviewsPerCustomer: 2,
  knowledgeUpdatesPerCustomer: 4,
  serviceHoursPerCustomer: 0,
  compliancePressure: 35,
  workloadVolatility: 45,
  supportComplexity: 35,
  privateDeployment: false,
  assuranceRequired: false,
});

export interface PublicPricingEvaluationResponse {
  evaluation: SovereignRouterXPricingEvaluation;
  ledger: {
    persisted: boolean;
    url: string;
    status?: number;
    error?: string;
  };
}

function getOpsConsoleBaseUrl(): string {
  return (process.env.OPS_CONSOLE_URL ?? process.env.PLATFORM_API_URL ?? 'http://localhost:4000').replace(/\/+$/, '');
}

export function evaluatePublicPricing(input: SovereignRouterXPricingInput | unknown, requestId?: string): SovereignRouterXPricingEvaluation {
  return evaluateSovereignRouterXPricing(input, {
    requestId,
  });
}

export function buildPricingLedgerEntry(evaluation: SovereignRouterXPricingEvaluation) {
  return createPricingLedgerEntry(evaluation);
}

export async function persistPricingLedgerEntry(
  evaluation: SovereignRouterXPricingEvaluation,
  fetchImpl: typeof fetch = fetch,
): Promise<PublicPricingEvaluationResponse['ledger']> {
  const url = `${getOpsConsoleBaseUrl()}/pricing/ledger`;
  try {
    const response = await fetchImpl(url, {
      method: 'POST',
      headers: {
        'content-type': 'application/json',
      },
      body: JSON.stringify({
        entry: createPricingLedgerEntry(evaluation),
      }),
    });

    if (!response.ok) {
      return {
        persisted: false,
        url,
        status: response.status,
      };
    }

    return {
      persisted: true,
      url,
      status: response.status,
    };
  } catch (error) {
    return {
      persisted: false,
      url,
      error: error instanceof Error ? error.message : String(error),
    };
  }
}

