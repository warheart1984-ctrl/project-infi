import { gridStyle, Metric, sectionStyle } from './shared.js';

type CustomerQuotaDashboard = {
  customer?: {
    id: string;
    email: string;
    planName: string;
    organizationId?: string;
    organizationRole?: string;
    entitlements: {
      routingTier: string;
      codexPacketHandoff: boolean;
      usageLedger: boolean;
      marginDashboard: boolean;
      auditScope: string;
    };
  };
  quota: {
    requestLimit: number;
    requestCount: number;
    requestOverage: number;
    tokenLimit: number;
    tokenCount: number;
    tokenOverage: number;
    overageBillingUsd: number;
    overageBillingEnabled: boolean;
    enforcement: {
      status: 'within_limit' | 'metered_overage' | 'blocked';
      allowed: boolean;
      reason: string;
    };
  };
  usageRecords: { operation: string; units: number; timestamp: string }[];
};

export interface CustomerQuotaEnforcementPanelProps {
  quota: CustomerQuotaDashboard | null;
}

export function CustomerQuotaEnforcementPanel({ quota }: CustomerQuotaEnforcementPanelProps) {
  return (
    <section id="customer-quota" style={sectionStyle}>
      <h2>Customer Quota Enforcement</h2>
      <p>Quota reporting mirrors the customer workspace so operators can see entitlement limits, overage billing, and blocked state in the same ledger view.</p>
      <div style={gridStyle}>
        <Metric label="Customer" value={quota?.customer?.email ?? 'loading'} />
        <Metric label="Requests" value={`${quota?.quota.requestCount ?? 0}/${quota?.quota.requestLimit ?? 0}`} />
        <Metric label="Tokens" value={`${quota?.quota.tokenCount ?? 0}/${quota?.quota.tokenLimit ?? 0}`} />
        <Metric label="Overage" value={formatCurrency(quota?.quota.overageBillingUsd ?? 0)} />
      </div>
      <p>{quota?.quota.enforcement.reason ?? 'Quota data is loading.'}</p>
      <table>
        <thead>
          <tr>
            <th>Operation</th>
            <th>Units</th>
            <th>Timestamp</th>
          </tr>
        </thead>
        <tbody>
          {(quota?.usageRecords ?? []).map((record, index) => (
            <tr key={`${record.operation}-${record.timestamp}-${index}`}>
              <td>{record.operation}</td>
              <td>{record.units}</td>
              <td>{record.timestamp}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}

function formatCurrency(value: number): string {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 2 }).format(value);
}
