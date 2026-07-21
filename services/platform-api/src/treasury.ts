import type { GovernanceMode, UsageRecord } from '@aaes-os/platform-core';

export type TreasuryRemittanceChannel = 'paypal-payouts' | 'openai-org-billing' | 'irs-direct-pay' | 'eftps';
export type PayPalEnvironment = 'sandbox' | 'live';

export interface TreasuryPayPalCheckoutAdapter {
  enabled: boolean;
  environment: PayPalEnvironment;
  apiBaseUrl: string;
  createOrderPath: '/v2/checkout/orders';
  captureOrderPath: '/v2/checkout/orders/:orderId/capture';
  orderRequest: {
    intent: 'CAPTURE';
    application_context: {
      brand_name: string;
      landing_page: 'NO_PREFERENCE';
      user_action: 'PAY_NOW';
      return_url: string;
      cancel_url: string;
    };
    purchase_units: Array<{
      reference_id: string;
      description: string;
      custom_id: string;
      amount: {
        currency_code: 'USD';
        value: string;
      };
    }>;
  };
}

export interface TreasuryPayPalPayoutAdapter {
  enabled: boolean;
  environment: PayPalEnvironment;
  apiBaseUrl: string;
  createBatchPath: '/v1/payments/payouts';
  batchRequest: {
    sender_batch_header: {
      sender_batch_id: string;
      email_subject: string;
      email_message: string;
    };
    items: Array<{
      recipient_type: 'EMAIL';
      amount: {
        currency: 'USD';
        value: string;
      };
      receiver: string;
      note: string;
      sender_item_id: string;
    }>;
  };
}

export interface TreasuryPayPalTransportResult {
  enabled: boolean;
  mode: 'preview' | 'live';
  environment: PayPalEnvironment;
  apiBaseUrl: string;
  request: Record<string, unknown>;
  response?: unknown;
  orderId?: string;
  batchId?: string;
  approvalUrl?: string;
  error?: string;
}

export interface TreasuryPlanInput {
  customerInvoiceUsd: number;
  openAiUsageCostUsd: number;
  taxRatePct: number;
  profitReservePct: number;
  platformReservePct: number;
  customerId: string;
  ownerId: string;
  governanceProfile: GovernanceMode;
}

export interface TreasuryAllocation {
  label: 'customer-payment' | 'openai-reserve' | 'tax-reserve' | 'platform-reserve' | 'owner-profit';
  amountUsd: number;
  destination: string;
  channel: TreasuryRemittanceChannel;
  notes: string;
}

export interface TreasuryPlan {
  customerId: string;
  ownerId: string;
  governanceProfile: GovernanceMode;
  grossInvoiceUsd: number;
  openAiUsageCostUsd: number;
  taxReserveUsd: number;
  platformReserveUsd: number;
  ownerProfitUsd: number;
  totalReserveUsd: number;
  netAfterReservesUsd: number;
  allocations: TreasuryAllocation[];
  remittanceInstructions: {
    openAI: {
      destination: 'OpenAI';
      channel: TreasuryRemittanceChannel;
      amountUsd: number;
      notes: string;
    };
    tax: {
      destination: 'IRS';
      channel: TreasuryRemittanceChannel;
      amountUsd: number;
      notes: string;
    };
    ownerProfit: {
      destination: 'PayPal';
      channel: TreasuryRemittanceChannel;
      amountUsd: number;
      notes: string;
    };
  };
  providerNotes: {
    customerCollection: string;
    openAI: string;
    tax: string;
    profit: string;
  };
  adapters: {
    paypalCheckout: TreasuryPayPalCheckoutAdapter;
    paypalPayout: TreasuryPayPalPayoutAdapter;
  };
  usageSnapshot?: {
    totalUnits: number;
    byOperation: Record<string, number>;
    byProfile: Record<GovernanceMode, number>;
    records: UsageRecord[];
  };
}

export interface TreasuryPaymentInstruction {
  destination: string;
  channel: TreasuryRemittanceChannel;
  amountUsd: number;
  notes: string;
}

export interface TreasuryPaymentSchedule {
  scheduledAt: string;
  source: 'ledger';
  customerId: string;
  ownerId: string;
  governanceProfile: GovernanceMode;
  instructions: {
    openAI: TreasuryPaymentInstruction;
    tax: TreasuryPaymentInstruction;
    ownerProfit: TreasuryPaymentInstruction;
  };
  sourcePlan: TreasuryPlan;
}

function round(value: number): number {
  return Math.round(value * 100) / 100;
}

function clamp(value: number, min: number, max: number): number {
  return Math.min(max, Math.max(min, value));
}

function isFiniteNumber(value: unknown): value is number {
  return typeof value === 'number' && Number.isFinite(value);
}

function normalizeInput(input: Partial<TreasuryPlanInput> & Pick<TreasuryPlanInput, 'customerId' | 'ownerId' | 'governanceProfile'>): TreasuryPlanInput {
  const customerInvoiceUsd = isFiniteNumber(input.customerInvoiceUsd) ? Math.max(0, input.customerInvoiceUsd) : 0;
  const openAiUsageCostUsd = isFiniteNumber(input.openAiUsageCostUsd) ? Math.max(0, input.openAiUsageCostUsd) : 0;
  const taxRatePct = clamp(isFiniteNumber(input.taxRatePct) ? input.taxRatePct : 22, 0, 100);
  const profitReservePct = clamp(isFiniteNumber(input.profitReservePct) ? input.profitReservePct : 18, 0, 100);
  const platformReservePct = clamp(isFiniteNumber(input.platformReservePct) ? input.platformReservePct : 8, 0, 100);

  return {
    customerInvoiceUsd: round(customerInvoiceUsd),
    openAiUsageCostUsd: round(openAiUsageCostUsd),
    taxRatePct: round(taxRatePct),
    profitReservePct: round(profitReservePct),
    platformReservePct: round(platformReservePct),
    customerId: input.customerId,
    ownerId: input.ownerId,
    governanceProfile: input.governanceProfile,
  };
}

function summarizeUsage(records: UsageRecord[]): TreasuryPlan['usageSnapshot'] {
  const byOperation: Record<string, number> = {};
  const byProfile: Record<GovernanceMode, number> = {
    strict: 0,
    balanced: 0,
    experimental: 0,
  };
  let totalUnits = 0;

  for (const record of records) {
    totalUnits += record.units;
    byOperation[record.operation] = (byOperation[record.operation] ?? 0) + record.units;
    byProfile[record.governanceProfile] += record.units;
  }

  return {
    totalUnits,
    byOperation,
    byProfile,
    records,
  };
}

function getPayPalEnvironment(): PayPalEnvironment {
  return String(process.env.PAYPAL_ENVIRONMENT ?? '').toLowerCase() === 'live' ? 'live' : 'sandbox';
}

function getPayPalApiBaseUrl(environment: PayPalEnvironment): string {
  return environment === 'live' ? 'https://api-m.paypal.com' : 'https://api-m.sandbox.paypal.com';
}

async function fetchPayPalAccessToken(environment: PayPalEnvironment, fetchImpl: typeof fetch = fetch): Promise<string | null> {
  const clientId = process.env.PAYPAL_CLIENT_ID?.trim();
  const clientSecret = process.env.PAYPAL_CLIENT_SECRET?.trim();
  if (!clientId || !clientSecret) {
    return null;
  }

  const response = await fetchImpl(`${getPayPalApiBaseUrl(environment)}/v1/oauth2/token`, {
    method: 'POST',
    headers: {
      authorization: `Basic ${Buffer.from(`${clientId}:${clientSecret}`).toString('base64')}`,
      'content-type': 'application/x-www-form-urlencoded',
      accept: 'application/json',
    },
    body: 'grant_type=client_credentials',
  });

  if (!response.ok) {
    const body = await response.text().catch(() => '');
    throw new Error(`PAYPAL: token request failed with HTTP ${response.status}${body ? ` (${body})` : ''}`);
  }

  const payload = (await response.json().catch(() => ({}))) as { access_token?: string };
  if (!payload.access_token) {
    throw new Error('PAYPAL: token response missing access_token');
  }

  return payload.access_token;
}

function formatUsd(value: number): string {
  return round(value).toFixed(2);
}

function buildPayPalCheckoutAdapter(planInput: TreasuryPlanInput): TreasuryPayPalCheckoutAdapter {
  const environment = getPayPalEnvironment();
  const returnUrl = process.env.PAYPAL_RETURN_URL ?? 'http://localhost:4000/treasury/paypal/return';
  const cancelUrl = process.env.PAYPAL_CANCEL_URL ?? 'http://localhost:4000/treasury/paypal/cancel';
  return {
    enabled: Boolean(process.env.PAYPAL_CLIENT_ID && process.env.PAYPAL_CLIENT_SECRET),
    environment,
    apiBaseUrl: getPayPalApiBaseUrl(environment),
    createOrderPath: '/v2/checkout/orders',
    captureOrderPath: '/v2/checkout/orders/:orderId/capture',
    orderRequest: {
      intent: 'CAPTURE',
      application_context: {
        brand_name: process.env.PAYPAL_BRAND_NAME ?? 'Sovereign Router X',
        landing_page: 'NO_PREFERENCE',
        user_action: 'PAY_NOW',
        return_url: returnUrl,
        cancel_url: cancelUrl,
      },
      purchase_units: [
        {
          reference_id: planInput.customerId,
          description: `Customer treasury collection for ${planInput.customerId}`,
          custom_id: `${planInput.customerId}:${planInput.ownerId}`,
          amount: {
            currency_code: 'USD',
            value: formatUsd(planInput.customerInvoiceUsd),
          },
        },
      ],
    },
  };
}

function buildPayPalPayoutAdapter(planInput: TreasuryPlanInput, ownerProfitUsd: number): TreasuryPayPalPayoutAdapter {
  const environment = getPayPalEnvironment();
  const payoutEmail = process.env.PAYPAL_PAYOUT_EMAIL ?? `${planInput.ownerId}@example.com`;
  return {
    enabled: Boolean(process.env.PAYPAL_CLIENT_ID && process.env.PAYPAL_CLIENT_SECRET),
    environment,
    apiBaseUrl: getPayPalApiBaseUrl(environment),
    createBatchPath: '/v1/payments/payouts',
    batchRequest: {
      sender_batch_header: {
        sender_batch_id: `${planInput.ownerId}-${Date.now().toString(36)}`,
        email_subject: 'Sovereign Router X owner payout',
        email_message: 'Your owner-profit payout has been scheduled from the treasury ledger.',
      },
      items: [
        {
          recipient_type: 'EMAIL',
          amount: {
            currency: 'USD',
            value: formatUsd(ownerProfitUsd),
          },
          receiver: payoutEmail,
          note: `Owner-profit distribution for ${planInput.ownerId}`,
          sender_item_id: `${planInput.customerId}:${planInput.ownerId}:owner-profit`,
        },
      ],
    },
  };
}

export async function executeTreasuryPayPalCheckout(
  planInput: TreasuryPlanInput,
  amountUsd: number = planInput.customerInvoiceUsd,
  fetchImpl: typeof fetch = fetch,
): Promise<TreasuryPayPalTransportResult> {
  const adapter = buildPayPalCheckoutAdapter(planInput);
  const request = {
    intent: adapter.orderRequest.intent,
    application_context: adapter.orderRequest.application_context,
    purchase_units: [
      {
        reference_id: planInput.customerId,
        description: `Customer treasury collection for ${planInput.customerId}`,
        custom_id: `${planInput.customerId}:${planInput.ownerId}`,
        amount: {
          currency_code: 'USD',
          value: formatUsd(amountUsd),
        },
      },
    ],
  };

  if (!adapter.enabled) {
    return {
      enabled: false,
      mode: 'preview',
      environment: adapter.environment,
      apiBaseUrl: adapter.apiBaseUrl,
      request,
    };
  }

  const accessToken = await fetchPayPalAccessToken(adapter.environment, fetchImpl);
  if (!accessToken) {
    return {
      enabled: false,
      mode: 'preview',
      environment: adapter.environment,
      apiBaseUrl: adapter.apiBaseUrl,
      request,
      error: 'PAYPAL: credentials are not configured',
    };
  }

  const response = await fetchImpl(`${adapter.apiBaseUrl}${adapter.createOrderPath}`, {
    method: 'POST',
    headers: {
      authorization: `Bearer ${accessToken}`,
      'content-type': 'application/json',
      accept: 'application/json',
    },
    body: JSON.stringify(request),
  });
  const responseBody = await response.json().catch(() => ({}));
  if (!response.ok) {
    return {
      enabled: true,
      mode: 'live',
      environment: adapter.environment,
      apiBaseUrl: adapter.apiBaseUrl,
      request,
      response: responseBody,
      error: `PAYPAL: create order failed with HTTP ${response.status}`,
    };
  }

  const approvalUrl =
    (responseBody as { links?: Array<{ rel?: string; href?: string }> }).links?.find((link) => link.rel === 'approve')?.href ??
    (responseBody as { links?: Array<{ rel?: string; href?: string }> }).links?.[0]?.href;

  return {
    enabled: true,
    mode: 'live',
    environment: adapter.environment,
    apiBaseUrl: adapter.apiBaseUrl,
    request,
    response: responseBody,
    orderId: typeof (responseBody as { id?: string }).id === 'string' ? (responseBody as { id?: string }).id : undefined,
    approvalUrl,
  };
}

export async function executeTreasuryPayPalPayout(
  planInput: TreasuryPlanInput,
  amountUsd: number,
  fetchImpl: typeof fetch = fetch,
): Promise<TreasuryPayPalTransportResult> {
  const adapter = buildPayPalPayoutAdapter(planInput, amountUsd);
  const request = adapter.batchRequest;

  if (!adapter.enabled) {
    return {
      enabled: false,
      mode: 'preview',
      environment: adapter.environment,
      apiBaseUrl: adapter.apiBaseUrl,
      request,
    };
  }

  const accessToken = await fetchPayPalAccessToken(adapter.environment, fetchImpl);
  if (!accessToken) {
    return {
      enabled: false,
      mode: 'preview',
      environment: adapter.environment,
      apiBaseUrl: adapter.apiBaseUrl,
      request,
      error: 'PAYPAL: credentials are not configured',
    };
  }

  const response = await fetchImpl(`${adapter.apiBaseUrl}${adapter.createBatchPath}`, {
    method: 'POST',
    headers: {
      authorization: `Bearer ${accessToken}`,
      'content-type': 'application/json',
      accept: 'application/json',
    },
    body: JSON.stringify(request),
  });
  const responseBody = await response.json().catch(() => ({}));
  if (!response.ok) {
    return {
      enabled: true,
      mode: 'live',
      environment: adapter.environment,
      apiBaseUrl: adapter.apiBaseUrl,
      request,
      response: responseBody,
      error: `PAYPAL: create payout batch failed with HTTP ${response.status}`,
    };
  }

  return {
    enabled: true,
    mode: 'live',
    environment: adapter.environment,
    apiBaseUrl: adapter.apiBaseUrl,
    request,
    response: responseBody,
    batchId: typeof (responseBody as { batch_header?: { payout_batch_id?: string } }).batch_header?.payout_batch_id === 'string'
      ? (responseBody as { batch_header?: { payout_batch_id?: string } }).batch_header?.payout_batch_id
      : undefined,
  };
}

export function createTreasuryPlan(
  input: Partial<TreasuryPlanInput> & Pick<TreasuryPlanInput, 'customerId' | 'ownerId' | 'governanceProfile'>,
  usageRecords: UsageRecord[] = [],
): TreasuryPlan {
  const planInput = normalizeInput(input);
  const platformReserveUsd = round(planInput.customerInvoiceUsd * (planInput.platformReservePct / 100));
  const openAiReserveUsd = round(Math.max(planInput.openAiUsageCostUsd, 0));
  const taxableBaseUsd = Math.max(0, planInput.customerInvoiceUsd - openAiReserveUsd - platformReserveUsd);
  const taxReserveUsd = round(taxableBaseUsd * (planInput.taxRatePct / 100));
  const grossAfterTaxUsd = Math.max(0, planInput.customerInvoiceUsd - openAiReserveUsd - platformReserveUsd - taxReserveUsd);
  const ownerProfitTargetUsd = round(grossAfterTaxUsd * (planInput.profitReservePct / 100));
  const ownerProfitUsd = round(Math.max(0, grossAfterTaxUsd - ownerProfitTargetUsd));
  const totalReserveUsd = round(openAiReserveUsd + taxReserveUsd + platformReserveUsd);
  const netAfterReservesUsd = round(Math.max(0, planInput.customerInvoiceUsd - totalReserveUsd));
  const usageSnapshot = usageRecords.length > 0 ? summarizeUsage(usageRecords) : undefined;

  return {
    customerId: planInput.customerId,
    ownerId: planInput.ownerId,
    governanceProfile: planInput.governanceProfile,
    grossInvoiceUsd: planInput.customerInvoiceUsd,
    openAiUsageCostUsd: openAiReserveUsd,
    taxReserveUsd,
    platformReserveUsd,
    ownerProfitUsd,
    totalReserveUsd,
    netAfterReservesUsd,
    allocations: [
      {
        label: 'customer-payment',
        amountUsd: planInput.customerInvoiceUsd,
        destination: 'Merchant account',
        channel: 'paypal-payouts',
        notes: 'Customer payment collected through the commercial checkout flow.',
      },
      {
        label: 'openai-reserve',
        amountUsd: openAiReserveUsd,
        destination: 'OpenAI',
        channel: 'openai-org-billing',
        notes: 'Reserve earmarked for OpenAI usage billing or prepaid credits.',
      },
      {
        label: 'tax-reserve',
        amountUsd: taxReserveUsd,
        destination: 'IRS',
        channel: 'irs-direct-pay',
        notes: 'Tax reserve to be remitted through IRS-approved payment rails such as Direct Pay, EFTPS, or an IRS-approved card or digital-wallet processor.',
      },
      {
        label: 'platform-reserve',
        amountUsd: platformReserveUsd,
        destination: 'Operating reserve',
        channel: 'paypal-payouts',
        notes: 'Platform reserve for fees, support, and cash buffering.',
      },
      {
        label: 'owner-profit',
        amountUsd: ownerProfitUsd,
        destination: 'Owner payout',
        channel: 'paypal-payouts',
        notes: 'Net owner profit available for payout after reserves are allocated.',
      },
    ],
    remittanceInstructions: {
      openAI: {
        destination: 'OpenAI',
        channel: 'openai-org-billing',
        amountUsd: openAiReserveUsd,
        notes: 'Pay OpenAI from the platform treasury or prepaid usage account.',
      },
      tax: {
        destination: 'IRS',
        channel: 'irs-direct-pay',
        amountUsd: taxReserveUsd,
        notes: 'Use IRS Direct Pay or EFTPS, or use PayPal only when the IRS payment processor flow explicitly supports it.',
      },
      ownerProfit: {
        destination: 'PayPal',
        channel: 'paypal-payouts',
        amountUsd: ownerProfitUsd,
        notes: 'Send profit distribution through PayPal Payouts or a business PayPal account.',
      },
    },
    providerNotes: {
      customerCollection: 'Collect customer payment through checkout, then record settlement in the treasury ledger.',
      openAI: 'OpenAI costs are separate vendor spend. Keep the treasury reserve aligned with your OpenAI billing cycle.',
      tax: 'IRS remittance should be scheduled through IRS-approved payment channels, not via PayPal.',
      // The tax reserve is an IRS payment instruction, not a PayPal payout.
      profit: 'Profit can be distributed to the owner through PayPal Payouts after reserves are held.',
    },
    adapters: {
      paypalCheckout: buildPayPalCheckoutAdapter(planInput),
      paypalPayout: buildPayPalPayoutAdapter(planInput, ownerProfitUsd),
    },
    usageSnapshot,
  };
}

export function createTreasuryPaymentSchedule(
  input: Partial<TreasuryPlanInput> & Pick<TreasuryPlanInput, 'customerId' | 'ownerId' | 'governanceProfile'>,
  usageRecords: UsageRecord[] = [],
  scheduledAt = new Date().toISOString(),
): TreasuryPaymentSchedule {
  const sourcePlan = createTreasuryPlan(input, usageRecords);
  return {
    scheduledAt,
    source: 'ledger',
    customerId: sourcePlan.customerId,
    ownerId: sourcePlan.ownerId,
    governanceProfile: sourcePlan.governanceProfile,
    instructions: {
      openAI: {
        destination: sourcePlan.remittanceInstructions.openAI.destination,
        channel: sourcePlan.remittanceInstructions.openAI.channel,
        amountUsd: sourcePlan.remittanceInstructions.openAI.amountUsd,
        notes: sourcePlan.remittanceInstructions.openAI.notes,
      },
      tax: {
        destination: sourcePlan.remittanceInstructions.tax.destination,
        channel: sourcePlan.remittanceInstructions.tax.channel,
        amountUsd: sourcePlan.remittanceInstructions.tax.amountUsd,
        notes: sourcePlan.remittanceInstructions.tax.notes,
      },
      ownerProfit: {
        destination: sourcePlan.remittanceInstructions.ownerProfit.destination,
        channel: sourcePlan.remittanceInstructions.ownerProfit.channel,
        amountUsd: sourcePlan.remittanceInstructions.ownerProfit.amountUsd,
        notes: sourcePlan.remittanceInstructions.ownerProfit.notes,
      },
    },
    sourcePlan,
  };
}
