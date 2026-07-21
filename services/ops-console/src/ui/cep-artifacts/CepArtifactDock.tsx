import type { CepArtifactExport, CepTrustBand, CepTrustGovernanceLevel } from './shared.js';
import {
  extractRouteDecisionArtifact,
  formatTrustScore,
  gridStyle,
  metricGridStyle,
  Panel,
  preStyle,
  sectionStyle,
  secondaryButtonStyle,
  subtleTextStyle,
  trustFieldStyle,
  trustFilterStyle,
  trustInputStyle,
  trustLabelStyle,
  Metric,
} from './shared.js';

export interface CepArtifactDockProps {
  cepArtifacts: CepArtifactExport;
  selectedCepArtifactId: string | null;
  onSelectedCepArtifactIdChange: (value: string) => void;
  cepTrustBandFilter: CepTrustBand | 'all';
  cepTrustGovernanceFilter: CepTrustGovernanceLevel | 'all';
  cepTrustMinScoreFilter: string;
  onCepTrustBandFilterChange: (value: CepTrustBand | 'all') => void;
  onCepTrustGovernanceFilterChange: (value: CepTrustGovernanceLevel | 'all') => void;
  onCepTrustMinScoreFilterChange: (value: string) => void;
}

export function CepArtifactDock({
  cepArtifacts,
  selectedCepArtifactId,
  onSelectedCepArtifactIdChange,
  cepTrustBandFilter,
  cepTrustGovernanceFilter,
  cepTrustMinScoreFilter,
  onCepTrustBandFilterChange,
  onCepTrustGovernanceFilterChange,
  onCepTrustMinScoreFilterChange,
}: CepArtifactDockProps) {
  const selectedArtifact =
    cepArtifacts.records.find((artifact) => artifact.id === selectedCepArtifactId) ??
    cepArtifacts.records.find((artifact) => artifact.id === cepArtifacts.viewState.selectedArtifactId) ??
    cepArtifacts.records[0] ??
    null;

  const selectedRouteDecision = extractRouteDecisionArtifact(selectedArtifact?.payload);
  const selectedKindRecords = selectedArtifact
    ? cepArtifacts.records.filter((artifact) => artifact.kind === selectedArtifact.kind)
    : cepArtifacts.records;

  return (
    <section id="cep-artifacts" style={sectionStyle}>
      <h2>CEP Artifact Dock</h2>
      <p>Promotion requests, replay jobs, and decisions are persisted to a JSONL artifact store and can be driven remotely by another orchestrator.</p>
      <div style={trustFilterStyle}>
        <label style={trustFieldStyle}>
          <span style={trustLabelStyle}>Trust band</span>
          <select
            value={cepTrustBandFilter}
            onChange={(event) => onCepTrustBandFilterChange(event.target.value as CepTrustBand | 'all')}
            style={trustInputStyle}
          >
            <option value="all">All bands</option>
            <option value="low">Low</option>
            <option value="medium">Medium</option>
            <option value="high">High</option>
          </select>
        </label>
        <label style={trustFieldStyle}>
          <span style={trustLabelStyle}>Governance</span>
          <select
            value={cepTrustGovernanceFilter}
            onChange={(event) => onCepTrustGovernanceFilterChange(event.target.value as CepTrustGovernanceLevel | 'all')}
            style={trustInputStyle}
          >
            <option value="all">All governance levels</option>
            <option value="basic">Basic</option>
            <option value="enhanced">Enhanced</option>
            <option value="full">Full</option>
          </select>
        </label>
        <label style={trustFieldStyle}>
          <span style={trustLabelStyle}>Minimum score</span>
          <input
            type="number"
            min={0}
            max={1}
            step={0.01}
            value={cepTrustMinScoreFilter}
            onChange={(event) => onCepTrustMinScoreFilterChange(event.target.value)}
            placeholder="0.75"
            style={trustInputStyle}
          />
        </label>
        <button
          type="button"
          onClick={() => {
            onCepTrustBandFilterChange('all');
            onCepTrustGovernanceFilterChange('all');
            onCepTrustMinScoreFilterChange('');
          }}
          style={secondaryButtonStyle}
        >
          Clear trust filters
        </button>
      </div>
      <div style={gridStyle}>
        <Metric label="Entries" value={String(cepArtifacts.entryCount)} />
        <Metric label="Promotion Requests" value={String(cepArtifacts.countsByKind['promotion-request'] ?? 0)} />
        <Metric label="Replay Jobs" value={String(cepArtifacts.countsByKind['replay-job'] ?? 0)} />
        <Metric label="Decisions" value={String(cepArtifacts.countsByKind.decision ?? 0)} />
        <Metric label="Trusted" value={String(cepArtifacts.trustSummary?.trustedCount ?? 0)} />
        <Metric label="Avg Trust" value={formatTrustScore(cepArtifacts.trustSummary?.averageTrustScore ?? null)} />
      </div>
      <div style={gridStyle}>
        <Panel title="Artifact Store">
          <p style={{ wordBreak: 'break-all' }}>{cepArtifacts.storePath}</p>
          <p>Remote selection {cepArtifacts.viewState.source}</p>
          <p>Selected kind {cepArtifacts.viewState.selectedKind}</p>
          <p>Selected artifact {cepArtifacts.viewState.selectedArtifactId ?? 'none'}</p>
          <p>Trust filter {cepArtifacts.trustFilters?.trustBand ?? cepTrustBandFilter} / {cepArtifacts.trustFilters?.governanceLevel ?? cepTrustGovernanceFilter}</p>
        </Panel>
        <Panel title="Artifact Summary">
          <ul>
            <li>Promotion requests: {cepArtifacts.countsByKind['promotion-request'] ?? 0}</li>
            <li>Replay jobs: {cepArtifacts.countsByKind['replay-job'] ?? 0}</li>
            <li>Decisions: {cepArtifacts.countsByKind.decision ?? 0}</li>
            <li>Trusted artifacts: {cepArtifacts.trustSummary?.trustedCount ?? 0}</li>
            <li>Untrusted artifacts: {cepArtifacts.trustSummary?.untrustedCount ?? 0}</li>
            <li>Average trust score: {formatTrustScore(cepArtifacts.trustSummary?.averageTrustScore ?? null)}</li>
          </ul>
        </Panel>
      </div>
      <table>
        <thead>
          <tr>
            <th>Kind</th>
            <th>Title</th>
            <th>Source</th>
            <th>Trust</th>
            <th>Recorded</th>
            <th>Related</th>
          </tr>
        </thead>
        <tbody>
          {selectedKindRecords.map((artifact) => (
            <tr key={artifact.id}>
              <td>
                <button
                  type="button"
                  onClick={() => onSelectedCepArtifactIdChange(artifact.id)}
                  style={{ ...secondaryButtonStyle, padding: '6px 10px' }}
                >
                  {artifact.kind}
                </button>
              </td>
              <td>{artifact.title}</td>
              <td>{artifact.source}</td>
              <td>{artifact.trust ? `${artifact.trust.band} (${artifact.trust.score.toFixed(2)})` : 'untrusted'}</td>
              <td>{artifact.recordedAt}</td>
              <td>{artifact.relatedArtifactId ?? 'none'}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <div style={gridStyle}>
        <Panel title="Selected Trust Packet">
          {selectedArtifact?.trust ? (
            <pre style={preStyle}>{JSON.stringify(selectedArtifact.trust, null, 2)}</pre>
          ) : (
            <p style={subtleTextStyle}>No trust packet is available for the selected artifact.</p>
          )}
        </Panel>
        <Panel title="Selected Trust Policy">
          {selectedArtifact?.trustPolicy ? (
            <pre style={preStyle}>{JSON.stringify(selectedArtifact.trustPolicy, null, 2)}</pre>
          ) : (
            <p style={subtleTextStyle}>No trust policy is attached to the selected artifact.</p>
          )}
        </Panel>
        <Panel title="Selected Route Decision">
          {selectedRouteDecision ? (
            <>
              <div style={metricGridStyle}>
                <Metric label="Decision" value={selectedRouteDecision.decisionId} />
                <Metric label="Request" value={selectedRouteDecision.requestId} />
                <Metric label="Governance" value={selectedRouteDecision.governanceResult} />
                <Metric label="Trust" value={`${selectedRouteDecision.trustBand} (${selectedRouteDecision.trustScore.toFixed(2)})`} />
              </div>
              <p style={subtleTextStyle}>{selectedRouteDecision.summary}</p>
              <pre style={preStyle}>{JSON.stringify(selectedRouteDecision.payload, null, 2)}</pre>
            </>
          ) : (
            <p style={subtleTextStyle}>No canonical route decision artifact is attached to the selected CEP artifact.</p>
          )}
        </Panel>
        <Panel title="Selected Artifact JSON">
          <pre style={preStyle}>{JSON.stringify(selectedArtifact, null, 2)}</pre>
        </Panel>
        <Panel title="Export Preview">
          <pre style={preStyle}>{JSON.stringify(cepArtifacts.recentRecords, null, 2)}</pre>
        </Panel>
      </div>
    </section>
  );
}
