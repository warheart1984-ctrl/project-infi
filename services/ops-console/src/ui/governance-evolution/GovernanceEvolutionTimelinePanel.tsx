import {
  Metric,
  Panel,
  preStyle,
  secondaryButtonStyle,
  sectionStyle,
  gridStyle,
  subtleTextStyle,
} from './shared.js';

type GovernanceEvolutionEntry = {
  eventId: string;
  stage: 'birth' | 'growth' | 'governance' | 'replay' | 'renewal';
  artifactId: string;
  createdAt: string;
  summary: string;
  outcome: 'proposed' | 'replayed' | 'amended' | 'validated';
  continuityReport: {
    reportId: string;
    createdAt: string;
    valid: boolean;
    lineageValid: boolean;
    replayValid: boolean;
    receiptId: string;
    notes: string[];
    chain: {
      sequence: number;
      entryType: string;
      subjectId: string;
      issuedAt: string;
      entryHash: string;
      previousHash: string | null;
    }[];
  };
  governanceDiff: null | {
    diffId: string;
    createdAt: string;
    currentConfigVersion: string;
    targetConfigVersion: string;
    domain: string;
    tier: string;
    changes: {
      path: string;
      before: unknown;
      after: unknown;
      rationale: string;
    }[];
    replayReportIds: string[];
    trustReportIds: string[];
  };
  replayReport: null | {
    replayId: string;
    mode: string;
    decision: string;
    stage: string;
    summary: string;
    receiptId: string;
    lawOfLawsEntryId: string;
  };
};

type GovernanceEvolutionTimeline = {
  timelineId: string;
  entries: GovernanceEvolutionEntry[];
  summary: {
    entryCount: number;
    continuityReports: number;
    governanceDiffs: number;
    replayReports: number;
    validatedAmendments: number;
  };
};

export interface GovernanceEvolutionTimelinePanelProps {
  governanceEvolution: GovernanceEvolutionTimeline;
  selectedGovernanceEvolutionId: string | null;
  onSelectedGovernanceEvolutionIdChange: (value: string) => void;
}

export function GovernanceEvolutionTimelinePanel({
  governanceEvolution,
  selectedGovernanceEvolutionId,
  onSelectedGovernanceEvolutionIdChange,
}: GovernanceEvolutionTimelinePanelProps) {
  const selectedGovernanceEvolutionEntry =
    governanceEvolution.entries.find((entry) => entry.eventId === selectedGovernanceEvolutionId) ??
    governanceEvolution.entries[0] ??
    null;

  return (
    <section id="governance-evolution" style={sectionStyle}>
      <h2>Governance Evolution Timeline</h2>
      <p>Continuity reports, replay validation, and governance diffs now live in one review surface so stewards can inspect lineage and amendment outcomes together.</p>
      <div style={gridStyle}>
        <Metric label="Events" value={String(governanceEvolution.summary.entryCount)} />
        <Metric label="Continuity Reports" value={String(governanceEvolution.summary.continuityReports)} />
        <Metric label="Governance Diffs" value={String(governanceEvolution.summary.governanceDiffs)} />
        <Metric label="Replay Reports" value={String(governanceEvolution.summary.replayReports)} />
      </div>
      <div style={gridStyle}>
        <Panel title="Timeline">
          <ul style={{ margin: 0, paddingLeft: 18 }}>
            {governanceEvolution.entries.map((entry) => (
              <li key={entry.eventId} style={{ marginBottom: 12 }}>
                <button
                  type="button"
                  onClick={() => onSelectedGovernanceEvolutionIdChange(entry.eventId)}
                  style={{ ...secondaryButtonStyle, marginBottom: 6 }}
                >
                  {entry.stage} - {entry.outcome} - {entry.summary}
                </button>
                <div style={subtleTextStyle}>
                  <span>Continuity {entry.continuityReport.valid ? 'valid' : 'review'}</span>
                  <span style={{ marginLeft: 12 }}>Replay {entry.replayReport ? entry.replayReport.decision : 'pending'}</span>
                  <span style={{ marginLeft: 12 }}>Diff {entry.governanceDiff ? entry.governanceDiff.diffId : 'none'}</span>
                </div>
              </li>
            ))}
          </ul>
        </Panel>
        <Panel title="Selected Continuity Report">
          {selectedGovernanceEvolutionEntry ? (
            <>
              <p><strong>Report:</strong> {selectedGovernanceEvolutionEntry.continuityReport.reportId}</p>
              <p><strong>Receipt:</strong> {selectedGovernanceEvolutionEntry.continuityReport.receiptId}</p>
              <p><strong>Lineage:</strong> {selectedGovernanceEvolutionEntry.continuityReport.lineageValid ? 'valid' : 'review'}</p>
              <p><strong>Replay:</strong> {selectedGovernanceEvolutionEntry.continuityReport.replayValid ? 'valid' : 'review'}</p>
              <ul>
                {selectedGovernanceEvolutionEntry.continuityReport.notes.map((note) => (
                  <li key={note}>{note}</li>
                ))}
              </ul>
              <pre style={preStyle}>
                {JSON.stringify(selectedGovernanceEvolutionEntry.continuityReport.chain, null, 2)}
              </pre>
            </>
          ) : (
            <p style={subtleTextStyle}>No continuity report selected.</p>
          )}
        </Panel>
        <Panel title="Selected Governance Diff">
          {selectedGovernanceEvolutionEntry?.governanceDiff ? (
            <>
              <p><strong>Diff:</strong> {selectedGovernanceEvolutionEntry.governanceDiff.diffId}</p>
              <p><strong>Versions:</strong> {selectedGovernanceEvolutionEntry.governanceDiff.currentConfigVersion} {"->"} {selectedGovernanceEvolutionEntry.governanceDiff.targetConfigVersion}</p>
              <p><strong>Domain:</strong> {selectedGovernanceEvolutionEntry.governanceDiff.domain}</p>
              <p><strong>Tier:</strong> {selectedGovernanceEvolutionEntry.governanceDiff.tier}</p>
              <ul>
                {selectedGovernanceEvolutionEntry.governanceDiff.changes.map((change) => (
                  <li key={`${change.path}-${selectedGovernanceEvolutionEntry.governanceDiff?.diffId}`}>
                    {change.path}: {String(change.before)} {"->"} {String(change.after)} ({change.rationale})
                  </li>
                ))}
              </ul>
              <p>Replay refs {selectedGovernanceEvolutionEntry.governanceDiff.replayReportIds.join(', ') || 'none'}</p>
              <p>Trust refs {selectedGovernanceEvolutionEntry.governanceDiff.trustReportIds.join(', ') || 'none'}</p>
            </>
          ) : (
            <p style={subtleTextStyle}>No governance diff available for the selected event.</p>
          )}
        </Panel>
        <Panel title="Selected Replay Report">
          {selectedGovernanceEvolutionEntry?.replayReport ? (
            <>
              <p><strong>Replay:</strong> {selectedGovernanceEvolutionEntry.replayReport.replayId}</p>
              <p><strong>Decision:</strong> {selectedGovernanceEvolutionEntry.replayReport.decision}</p>
              <p><strong>Stage:</strong> {selectedGovernanceEvolutionEntry.replayReport.stage}</p>
              <p>{selectedGovernanceEvolutionEntry.replayReport.summary}</p>
              <pre style={preStyle}>
                {JSON.stringify({
                  receiptId: selectedGovernanceEvolutionEntry.replayReport.receiptId,
                  lawOfLawsEntryId: selectedGovernanceEvolutionEntry.replayReport.lawOfLawsEntryId,
                }, null, 2)}
              </pre>
            </>
          ) : (
            <p style={subtleTextStyle}>No replay report attached to the selected event.</p>
          )}
        </Panel>
      </div>
    </section>
  );
}
