import React, { useEffect, useState } from 'react';

import { PatchApprovals } from './PatchApprovals.js';

type DriftScore = {
  score: number;
  totalFaults: number;
  uniquePatterns: number;
  topPatterns?: PatternRecord[];
};

type PatternRecord = {
  patternId: string;
  faultCodes: string[];
  invariantIds?: string[];
  recurrence: number;
  firstSeenAt: string;
  lastSeenAt: string;
};

type FaultEvent = {
  faultId: string;
  runId: string;
  spanId: string;
  invariantId?: string;
  timestamp: string;
  faultCode: string;
  severity: string;
};

type PatchPoint = {
  patchId: string;
  timestamp: string;
  effectiveness: number;
};

type TelemetryResponse = {
  drift: DriftScore;
  topPatterns: PatternRecord[];
  lastFaults: FaultEvent[];
  patchTimeline?: PatchPoint[];
};

type ScoreVector = {
  continuity: number;
  governance: number;
  memory: number;
  coordination: number;
  confidence: number;
};

type MriV2Response = {
  state_vector: ScoreVector;
  delta_state: ScoreVector;
  trajectory_vector: {
    continuity: number;
    governance: number;
    memory: number;
    coordination: number;
    magnitude: number;
    confidenceWeightedMagnitude: number;
    confidence_weighted_magnitude: number;
  };
  benchmarks: {
    industryAverage: ScoreVector;
    topQuartile: ScoreVector;
    previousMeasurement: ScoreVector;
    summary: string;
    deltas: { dimension: keyof ScoreVector; vsPrevious: number; vsIndustry: number; vsTopQuartile: number }[];
    bar_markers: Record<keyof ScoreVector, { current: number; previous: number; industry: number; topQuartile: number }>;
  };
  trajectory_signatures: string[];
  trajectory_breakdown: { dimension: keyof ScoreVector; delta: number; confidence: number; contribution: number; direction: string }[];
  projection: ScoreVector[];
  risks: { id: string; type: string; description: string }[];
  interventions: { id: string; type: string; description: string; score: number }[];
  evidence: { beforeConfidence: number; afterConfidence: number; meanConfidence: number; confidenceTensor: Record<string, number> };
  before_after: { before: ScoreVector; after: ScoreVector };
};

type EnforcementSummary = {
  status: string;
  events: { receiptId: string; verdict: string; reasonCode: string; transitionId?: string }[];
  invariantSet?: { active: number; disabled: number };
  tokenCounts?: Record<string, number>;
  enforcementRatePerMinute?: number;
  replayAttemptsBlocked?: number;
};

type MetaSummary = {
  podId: string;
  generativeCoreId: string;
  metaInvariantCount: number;
};

type LoadedState = {
  telemetry: TelemetryResponse;
  mriV2: MriV2Response;
  enforcement: EnforcementSummary;
  meta: MetaSummary;
};

export const App: React.FC = () => {
  const [state, setState] = useState<LoadedState | null>(null);

  useEffect(() => {
    const fetchTelemetry = async () => {
      const [telemetryRes, mriRes, enforcementRes, metaRes] = await Promise.all([
        fetch('/telemetry'),
        fetch('/mri/v2'),
        fetch('/cen/events'),
        fetch('/pod/meta_constitutional_collapse'),
      ]);
      const telemetry = (await telemetryRes.json()) as TelemetryResponse;
      const mriV2 = (await mriRes.json()) as MriV2Response;
      const enforcement = (await enforcementRes.json()) as EnforcementSummary;
      const metaPayload = (await metaRes.json()) as {
        pod: { podId: string };
        collapse: { generativeCoreId: string; metaInvariants: unknown[] };
      };
      setState({
        telemetry,
        mriV2,
        enforcement,
        meta: {
          podId: metaPayload.pod.podId,
          generativeCoreId: metaPayload.collapse.generativeCoreId,
          metaInvariantCount: metaPayload.collapse.metaInvariants.length,
        },
      });
    };
    fetchTelemetry();
    const id = setInterval(fetchTelemetry, 5000);
    return () => clearInterval(id);
  }, []);

  if (!state) return <div>Loading telemetry...</div>;
  return <OpsConsoleView {...state} />;
};

export const OpsConsoleView: React.FC<LoadedState> = ({ telemetry, mriV2, enforcement, meta }) => (
  <div style={{ fontFamily: 'system-ui', padding: 16, color: '#172026', background: '#f6f7f9' }}>
    <h1 style={{ margin: '0 0 16px' }}>AAES-OS Ops Console</h1>
    <nav style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 16 }}>
      <a href="#mri">MRI Cockpit</a>
      <a href="#enforcement">Enforcement Dashboard</a>
      <a href="#meta">Meta-Constitutional Console</a>
    </nav>

    <section id="mri" style={sectionStyle}>
      <h2>MRI Cockpit</h2>
      <p>{mriV2.benchmarks.summary}</p>
      <div style={gridStyle}>
        {(['continuity', 'governance', 'memory', 'coordination', 'confidence'] as const).map((dimension) => (
          <BenchmarkCard
            key={dimension}
            label={dimension}
            score={mriV2.state_vector[dimension]}
            delta={mriV2.delta_state[dimension]}
            markers={mriV2.benchmarks.bar_markers[dimension]}
          />
        ))}
      </div>
      <div style={gridStyle}>
        <Panel title="Risk Register">
          <ul>{mriV2.risks.map((risk) => <li key={risk.id}>{risk.type}: {risk.description}</li>)}</ul>
        </Panel>
        <Panel title="Intervention Ranking">
          <ol>{mriV2.interventions.slice(0, 3).map((item) => <li key={item.id}>{item.type} ({item.score})</li>)}</ol>
        </Panel>
        <Panel title="Trajectory">
          <p>Magnitude {mriV2.trajectory_vector.magnitude.toFixed(3)}</p>
          <p>Weighted {mriV2.trajectory_vector.confidence_weighted_magnitude.toFixed(3)}</p>
          <p>{mriV2.trajectory_signatures.join(', ')}</p>
        </Panel>
        <Panel title="Evidence Ledger">
          <p>Mean confidence {mriV2.evidence.meanConfidence.toFixed(3)}</p>
          <p>Before {mriV2.evidence.beforeConfidence} | After {mriV2.evidence.afterConfidence}</p>
        </Panel>
      </div>
    </section>

    <section id="enforcement" style={sectionStyle}>
      <h2>Enforcement Dashboard</h2>
      <div style={gridStyle}>
        <Metric label="CEN" value={enforcement.status} />
        <Metric label="Invariant Set" value={`${enforcement.invariantSet?.active ?? 0} active`} />
        <Metric label="Rate" value={`${enforcement.enforcementRatePerMinute ?? 0}/min`} />
        <Metric label="Replay Blocks" value={String(enforcement.replayAttemptsBlocked ?? 0)} />
      </div>
      <table>
        <thead><tr><th>Receipt</th><th>Verdict</th><th>Reason</th></tr></thead>
        <tbody>
          {enforcement.events.map((event) => (
            <tr key={event.receiptId}><td>{event.receiptId}</td><td>{event.verdict}</td><td>{event.reasonCode}</td></tr>
          ))}
        </tbody>
      </table>
    </section>

    <section id="meta" style={sectionStyle}>
      <h2>Meta-Constitutional Console</h2>
      <div style={gridStyle}>
        <Metric label="POD" value={meta.podId} />
        <Metric label="Core" value={meta.generativeCoreId} />
        <Metric label="Meta-Invariants" value={String(meta.metaInvariantCount)} />
        <Metric label="Drift" value={telemetry.drift.score.toFixed(3)} />
      </div>
    </section>

    <section style={sectionStyle}>
      <h2>Top Patterns</h2>
      <table>
        <thead><tr><th>Pattern</th><th>Fault codes</th><th>Recurrence</th><th>Last seen</th></tr></thead>
        <tbody>
          {telemetry.topPatterns.map((pattern) => (
            <tr key={pattern.patternId}>
              <td>{pattern.patternId}</td>
              <td>{pattern.faultCodes.join(', ')}</td>
              <td>{pattern.recurrence}</td>
              <td>{pattern.lastSeenAt}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>

    <PatchApprovals apiBase="" />
  </div>
);

const sectionStyle: React.CSSProperties = {
  background: '#fff',
  border: '1px solid #dfe3e8',
  borderRadius: 8,
  padding: 16,
  marginBottom: 16,
};

const gridStyle: React.CSSProperties = {
  display: 'grid',
  gap: 12,
  gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
};

const Panel: React.FC<{ title: string; children: React.ReactNode }> = ({ title, children }) => (
  <div style={{ border: '1px solid #e3e7ed', borderRadius: 6, padding: 12 }}>
    <h3 style={{ marginTop: 0 }}>{title}</h3>
    {children}
  </div>
);

const Metric: React.FC<{ label: string; value: string }> = ({ label, value }) => (
  <div style={{ border: '1px solid #e3e7ed', borderRadius: 6, padding: 12 }}>
    <div style={{ color: '#5f6b7a', fontSize: 12, textTransform: 'uppercase' }}>{label}</div>
    <div style={{ fontSize: 20, fontWeight: 700 }}>{value}</div>
  </div>
);

const BenchmarkCard: React.FC<{
  label: string;
  score: number;
  delta: number;
  markers: { current: number; previous: number; industry: number; topQuartile: number };
}> = ({ label, score, delta, markers }) => (
  <div style={{ border: '1px solid #e3e7ed', borderRadius: 6, padding: 12 }}>
    <div style={{ color: '#5f6b7a', fontSize: 12, textTransform: 'uppercase' }}>{label}</div>
    <div style={{ fontSize: 28, fontWeight: 700 }}>{score}</div>
    <div style={{ height: 8, background: '#e8edf2', borderRadius: 4, position: 'relative', margin: '8px 0' }}>
      <span style={markerStyle(markers.industry, '#677483')} />
      <span style={markerStyle(markers.previous, '#9aa5b1')} />
      <span style={markerStyle(markers.topQuartile, '#2f6fed')} />
      <span style={markerStyle(markers.current, '#138a5e', 8)} />
    </div>
    <div>Delta {formatDelta(delta)}</div>
  </div>
);

function markerStyle(value: number, color: string, size = 6): React.CSSProperties {
  return {
    position: 'absolute',
    left: `${Math.max(0, Math.min(100, value))}%`,
    top: '50%',
    width: size,
    height: size,
    background: color,
    borderRadius: '50%',
    transform: 'translate(-50%, -50%)',
  };
}

function formatDelta(value: number): string {
  return value >= 0 ? `+${value}` : String(value);
}
