export interface TreasuryStore {
  getOrgBalance(orgId: string): Promise<{ balance: number; currency: string }>;
  recordCharge(orgId: string, amount: number, currency: string, metadata?: unknown): Promise<void>;
  recordPayout(orgId: string, amount: number, currency: string, metadata?: unknown): Promise<void>;
}

export interface CheckoutSession {
  id: string;
  orgId: string;
  amount: number;
  currency: string;
  provider: 'paypal';
  url: string;
}

export interface PayoutInstruction {
  id: string;
  orgId: string;
  amount: number;
  currency: string;
  provider: 'paypal';
}

export interface TreasuryPaymentInstruction {
  destination: string;
  channel: 'paypal-payouts' | 'openai-org-billing' | 'irs-direct-pay' | 'eftps';
  amountUsd: number;
  notes: string;
}
