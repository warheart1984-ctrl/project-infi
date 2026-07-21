import type { ConstitutionalEvidenceGraphSummary } from '@aaes-os/aaes-governance';

import { gridStyle, Metric, sectionStyle } from './shared.js';

export interface ConstitutionalEvidenceGraphPanelProps {
  evidenceGraph?: ConstitutionalEvidenceGraphSummary;
}

export function ConstitutionalEvidenceGraphPanel({ evidenceGraph }: ConstitutionalEvidenceGraphPanelProps) {
  return (
    <section style={sectionStyle}>
      <h2>Constitutional Evidence Graph</h2>
      <p>The evidence graph resolves the release receipt into the proof-surface and public-view nodes used by every operator surface.</p>
      <div style={gridStyle}>
        <Metric label="Graph ID" value={evidenceGraph?.graphId ?? 'loading'} />
        <Metric label="Root Receipt" value={evidenceGraph?.rootReceiptId ?? 'loading'} />
        <Metric label="Claims" value={String(evidenceGraph?.claimCount ?? 0)} />
        <Metric label="Unresolved" value={String(evidenceGraph?.unresolvedClaims.length ?? 0)} />
      </div>
      <p style={{ marginBottom: 0, color: '#5f6b7a' }}>
        Public claims resolve through the same evidence graph before they appear in dashboards or docs.
      </p>
    </section>
  );
}
