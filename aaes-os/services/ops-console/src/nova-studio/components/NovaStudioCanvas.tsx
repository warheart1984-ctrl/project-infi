import type { CSSProperties, ReactNode } from 'react';

import { CapabilityTable } from './CapabilityTable.js';
import { ControlTower } from './ControlTower.js';
import { DriftVisualizer } from './DriftVisualizer.js';
import { ReceiptFeed } from './ReceiptFeed.js';
import { ReplayPanel } from './ReplayPanel.js';
import { createGovernanceEnvelope } from '../governance/envelope.js';
import { evaluateGovernanceEnvelope } from '../governance/invariants.js';
import { useGovernanceReceipts } from '../hooks/useGovernanceReceipts.js';
import { useOperatorIdentity } from '../hooks/useOperatorIdentity.js';
import { useSubstrateEvents } from '../hooks/useSubstrateEvents.js';
import { studioRoutes } from '../routes.js';
import { OperatorContextProvider } from '../state/operatorContext.js';
import { createOperatorContext, type EnforcementSummary, type SkillzMcgeeLedgerSummary } from '../state/studioState.js';

export function NovaStudioCanvas({
  enforcement,
  skillzmcgee,
}: {
  enforcement: EnforcementSummary;
  skillzmcgee: SkillzMcgeeLedgerSummary;
}) {
  const operatorId = useOperatorIdentity();
  const substrate = useSubstrateEvents(skillzmcgee);
  const governanceReceipts = useGovernanceReceipts(skillzmcgee, enforcement);
  const operatorContext = createOperatorContext({
    operatorId,
    mode: 'coding-agent',
    skillzmcgee,
  });
  const envelope = skillzmcgee.capabilities[0]
    ? createGovernanceEnvelope({
      operatorContext,
      capability: skillzmcgee.capabilities[0],
      input: { capability: skillzmcgee.capabilities[0].name, checkpoint: operatorContext.continuity.checkpoint },
      status: 'pending',
    })
    : null;
  const invariantFailures = envelope
    ? evaluateGovernanceEnvelope(envelope, { capabilities: skillzmcgee.capabilities, receiptCount: skillzmcgee.receiptCount })
    : [];

  return (
    <OperatorContextProvider value={operatorContext}>
      <section id="nova-studio" style={sectionStyle}>
        <header>
          <h2>Nova Studio</h2>
          <nav style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 12 }}>
            {studioRoutes.filter((route) => route.path !== '/nova/studio').map((route) => (
              <a key={route.path} href={`#${route.path}`}>{route.label}</a>
            ))}
          </nav>
        </header>
        <div style={gridStyle}>
          <Metric label="Mode" value="Coding Agent" />
          <Metric label="Ledger" value={skillzmcgee.available ? 'live' : 'offline'} />
          <Metric label="Receipts" value={String(skillzmcgee.receiptCount)} />
          <Metric label="Law Spine" value={enforcement.status} />
        </div>
        <div style={{ ...gridStyle, gridTemplateColumns: 'repeat(auto-fit, minmax(min(280px, 100%), 1fr))' }}>
          <Panel title="Reasoning Corridor">
            {skillzmcgee.error ? <p>{skillzmcgee.error}</p> : null}
            <p>Source {skillzmcgee.source}</p>
            {Object.entries(skillzmcgee.state).slice(0, 4).length > 0 ? (
              <ul>
                {Object.entries(skillzmcgee.state).slice(0, 4).map(([slice, state]) => (
                  <li key={slice}>{slice}: {state.last_status} via {state.last_run_id}</li>
                ))}
              </ul>
            ) : (
              <p>No SkillzMcGee slice state recorded yet.</p>
            )}
          </Panel>
          <Panel title="Capability Calls">
            <CapabilityTable capabilities={skillzmcgee.capabilities} state={skillzmcgee.state} />
          </Panel>
        </div>
        <div style={{ ...gridStyle, gridTemplateColumns: 'repeat(auto-fit, minmax(min(260px, 100%), 1fr))' }}>
          <Panel title="Drift Visualizer">
            <DriftVisualizer skillzmcgee={skillzmcgee} />
          </Panel>
          <Panel title="Control Tower">
            <ControlTower operatorContext={operatorContext} />
          </Panel>
          <Panel title="Replay & Receipts">
            <ReplayPanel checkpoints={substrate.replayCheckpoints} timeline={substrate.timeline} />
          </Panel>
        </div>
        <Panel title="Governance Envelope">
          <p>Operator {operatorContext.operatorId}</p>
          <p>Continuity {operatorContext.continuity.checkpoint}</p>
          <p>Envelope {envelope?.status ?? 'pending'} {envelope?.inputHash ?? 'no-input'}</p>
          <p>Invariants {invariantFailures.length === 0 ? 'pass' : invariantFailures.join(', ')}</p>
          <p>Governance receipts {governanceReceipts.length}</p>
        </Panel>
        <Panel title="Recent SkillzMcGee Receipts">
          <ReceiptFeed receipts={skillzmcgee.recentReceipts} />
        </Panel>
      </section>
    </OperatorContextProvider>
  );
}

const sectionStyle: CSSProperties = {
  background: '#fff',
  border: '1px solid #dfe3e8',
  borderRadius: 8,
  padding: 16,
  marginBottom: 16,
};

const gridStyle: CSSProperties = {
  display: 'grid',
  gap: 12,
  gridTemplateColumns: 'repeat(auto-fit, minmax(min(180px, 100%), 1fr))',
};

const Panel = ({ title, children }: { title: string; children: ReactNode }) => (
  <div style={{ border: '1px solid #e3e7ed', borderRadius: 6, padding: 12 }}>
    <h3 style={{ marginTop: 0 }}>{title}</h3>
    {children}
  </div>
);

const Metric = ({ label, value }: { label: string; value: string }) => (
  <div style={{ border: '1px solid #e3e7ed', borderRadius: 6, padding: 12 }}>
    <div style={{ color: '#5f6b7a', fontSize: 12, textTransform: 'uppercase' }}>{label}</div>
    <div style={{ fontSize: 20, fontWeight: 700 }}>{value}</div>
  </div>
);
