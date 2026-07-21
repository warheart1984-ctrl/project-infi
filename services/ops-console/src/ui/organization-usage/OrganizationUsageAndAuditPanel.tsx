import { formatCurrency, gridStyle, Metric, Panel, preStyle, sectionStyle } from './shared.js';

type OrganizationUsageDashboard = {
  organizationId: string;
  total: number;
  byKind: Record<string, number>;
  summary: {
    total: number;
    byKind: Record<string, number>;
  };
  overageEvents: {
    id: string;
    kind: string;
    amount: number;
    occurredAt: string;
    metadata?: Record<string, unknown>;
  }[];
};

type OrganizationAuditDashboard = {
  organizationId: string;
  pricing: unknown[];
  routing: unknown[];
  entitlements: unknown[];
};

export interface OrganizationUsageAndAuditPanelProps {
  organizationUsage: OrganizationUsageDashboard | null;
  organizationAudit: OrganizationAuditDashboard | null;
}

export function OrganizationUsageAndAuditPanel({ organizationUsage, organizationAudit }: OrganizationUsageAndAuditPanelProps) {
  return (
    <section id="org-usage" style={sectionStyle}>
      <h2>Organization Usage and Audit</h2>
      <p>Operators can inspect org-scoped usage totals, overage events, and the pricing, routing, and entitlements audit packets that justify customer state.</p>
      <div style={gridStyle}>
        <Metric label="Organization" value={organizationUsage?.organizationId ?? organizationAudit?.organizationId ?? 'loading'} />
        <Metric label="Usage total" value={String(organizationUsage?.total ?? 0)} />
        <Metric label="Overage events" value={String(organizationUsage?.overageEvents.length ?? 0)} />
        <Metric label="Audit packets" value={String((organizationAudit?.pricing.length ?? 0) + (organizationAudit?.routing.length ?? 0) + (organizationAudit?.entitlements.length ?? 0))} />
      </div>
      <div style={gridStyle}>
        <Panel title="Usage by kind">
          <table>
            <thead>
              <tr>
                <th>Kind</th>
                <th>Units</th>
              </tr>
            </thead>
            <tbody>
              {(Object.entries((organizationUsage?.byKind ?? {}) as Record<string, number>) as Array<[string, number]>).map(([kind, amount]) => (
                <tr key={kind}>
                  <td>{kind}</td>
                  <td>{amount}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Panel>
        <Panel title="Overage events">
          <table>
            <thead>
              <tr>
                <th>Kind</th>
                <th>Amount</th>
                <th>Occurred</th>
              </tr>
            </thead>
            <tbody>
              {(organizationUsage?.overageEvents ?? []).map((event: NonNullable<OrganizationUsageDashboard['overageEvents']>[number]) => (
                <tr key={event.id}>
                  <td>{event.kind}</td>
                  <td>{formatCurrency(event.amount)}</td>
                  <td>{event.occurredAt}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Panel>
      </div>
      <div style={gridStyle}>
        <Panel title="Pricing audit">
          <pre style={preStyle}>{JSON.stringify(organizationAudit?.pricing ?? [], null, 2)}</pre>
        </Panel>
        <Panel title="Routing audit">
          <pre style={preStyle}>{JSON.stringify(organizationAudit?.routing ?? [], null, 2)}</pre>
        </Panel>
        <Panel title="Entitlements audit">
          <pre style={preStyle}>{JSON.stringify(organizationAudit?.entitlements ?? [], null, 2)}</pre>
        </Panel>
      </div>
    </section>
  );
}
