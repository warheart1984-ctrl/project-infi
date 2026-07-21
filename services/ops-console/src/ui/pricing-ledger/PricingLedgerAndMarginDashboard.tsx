import { formatCurrency, gridStyle, Metric, Panel, preStyle, sectionStyle, subtleTextStyle } from './shared.js';

type PricingLedgerEntry = {
  requestId: string;
  recordedAt: string;
  segment: string;
  strategy: string;
  routedRequests: number;
  monthlyCustomers: number;
  estimatedRevenueUsd: number;
  estimatedCostUsd: number;
  estimatedGrossMarginUsd: number;
  estimatedGrossMarginPct: number;
  selectedModel: string;
  backend: string;
  routeReason: string;
};

type PricingLedgerSummary = {
  available: boolean;
  storePath: string;
  entryCount: number;
  totalRevenueUsd: number;
  totalCostUsd: number;
  totalGrossMarginUsd: number;
  grossMarginPct: number;
  recentEntries: PricingLedgerEntry[];
  bySegment: {
    segment: string;
    entryCount: number;
    revenueUsd: number;
    costUsd: number;
    grossMarginUsd: number;
    grossMarginPct: number;
  }[];
  byStrategy: {
    strategy: string;
    entryCount: number;
    revenueUsd: number;
    costUsd: number;
    grossMarginUsd: number;
    grossMarginPct: number;
  }[];
  cohortHistory: {
    cohort: string;
    entryCount: number;
    revenueUsd: number;
    costUsd: number;
    grossMarginUsd: number;
    grossMarginPct: number;
    strategyMix: string[];
  }[];
};

export interface PricingLedgerAndMarginDashboardProps {
  pricing?: PricingLedgerSummary | null;
}

export function PricingLedgerAndMarginDashboard({ pricing }: PricingLedgerAndMarginDashboardProps) {
  return (
    <section id="pricing" style={sectionStyle}>
      <h2>Pricing Ledger and Margin Dashboard</h2>
      <p>The console now receives routed-request economics from the same Sovereign Router X pricing path used by the public website.</p>
      <div style={gridStyle}>
        <Metric label="Ledger" value={pricing?.available ? 'available' : 'empty'} />
        <Metric label="Entries" value={String(pricing?.entryCount ?? 0)} />
        <Metric label="Revenue" value={formatCurrency(pricing?.totalRevenueUsd ?? 0)} />
        <Metric label="Margin" value={`${formatCurrency(pricing?.totalGrossMarginUsd ?? 0)} (${(pricing?.grossMarginPct ?? 0).toFixed(1)}%)`} />
      </div>
      <div style={gridStyle}>
        <Panel title="Ledger Path">
          <p style={{ wordBreak: 'break-all' }}>{pricing?.storePath ?? 'loading'}</p>
          <p>Direct cost {formatCurrency(pricing?.totalCostUsd ?? 0)}</p>
          <p><a href="/pricing/reports/margin.csv">Download margin report CSV</a></p>
          <p><a href="/pricing/reports/cohorts.csv">Download cohort history CSV</a></p>
        </Panel>
        <Panel title="By Segment">
          <ul>
            {(pricing?.bySegment ?? []).map((row) => (
              <li key={row.segment}>
                {row.segment}: {row.entryCount} entries, {formatCurrency(row.grossMarginUsd)} margin
              </li>
            ))}
          </ul>
        </Panel>
        <Panel title="By Strategy">
          <ul>
            {(pricing?.byStrategy ?? []).map((row) => (
              <li key={row.strategy}>
                {row.strategy}: {row.entryCount} entries, {row.grossMarginPct.toFixed(1)}% margin
              </li>
            ))}
          </ul>
        </Panel>
        <Panel title="Cohort History">
          <ul>
            {(pricing?.cohortHistory ?? []).map((row) => (
              <li key={row.cohort}>
                {row.cohort}: {row.entryCount} entries, {formatCurrency(row.grossMarginUsd)} margin, mix {row.strategyMix.join(', ') || 'none'}
              </li>
            ))}
          </ul>
        </Panel>
      </div>
      <table>
        <thead>
          <tr>
            <th>Request</th>
            <th>Segment</th>
            <th>Strategy</th>
            <th>Model</th>
            <th>Revenue</th>
            <th>Margin</th>
          </tr>
        </thead>
        <tbody>
          {(pricing?.recentEntries ?? []).map((entry) => (
            <tr key={entry.requestId}>
              <td>{entry.requestId}</td>
              <td>{entry.segment}</td>
              <td>{entry.strategy}</td>
              <td>{entry.selectedModel} / {entry.backend}</td>
              <td>{formatCurrency(entry.estimatedRevenueUsd)}</td>
              <td>{formatCurrency(entry.estimatedGrossMarginUsd)} ({entry.estimatedGrossMarginPct.toFixed(1)}%)</td>
            </tr>
          ))}
        </tbody>
      </table>
      <p style={subtleTextStyle}>Pricing ledger entries are the same governed economics used by the public website, the router, and the operator margin views.</p>
      <pre style={preStyle}>{JSON.stringify(pricing?.recentEntries ?? [], null, 2)}</pre>
    </section>
  );
}
