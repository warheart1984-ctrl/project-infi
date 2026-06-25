import React from 'react';
import { EvidenceGraph } from './EvidenceGraph';

const LAYER_LEGEND = [
  { layer: 'law', label: 'Law', color: '#f5c542' },
  { layer: 'cit', label: 'CIT', color: '#6cb6ff' },
  { layer: 'mit', label: 'MIT', color: '#c792ea' },
  { layer: 'sit', label: 'SIT', color: '#7aa2f7' },
  { layer: 'git', label: 'GIT', color: '#bb9af7' },
  { layer: 'pit', label: 'PIT', color: '#e0af68' },
  { layer: 'eit', label: 'EIT', color: '#3dd68c' },
  { layer: 'evidence', label: 'Evidence', color: '#4fd1c5' },
  { layer: 'lineage', label: 'Lineage', color: '#8fa0bf' },
];

export function CrossLedgerTracePanel({ trace, loading, stewardMode, onNodeClick }) {
  if (loading) {
    return <div className="constitutional-panel cross-ledger-trace">Loading cross-ledger trace…</div>;
  }

  if (!trace?.found) {
    return null;
  }

  const graphNodes = (trace.nodes || []).map((node) => ({
    ...node,
    type: node.layer || node.type || 'trace',
    label: node.label || node.id,
  }));

  return (
    <section className="constitutional-panel cross-ledger-trace">
      <header className="cross-ledger-trace-header">
        <h3>Cross-Ledger Trace</h3>
        <span className="constitutional-muted">
          {trace.law_id} · epoch {trace.epoch}
          {trace.chi != null ? ` · Χ=${Number(trace.chi).toFixed(3)}` : ''}
          {trace.mu != null ? ` · Μ=${Number(trace.mu).toFixed(3)}` : ''}
        </span>
      </header>

      {!stewardMode ? (
        <>
          <div className="cross-ledger-legend">
            {LAYER_LEGEND.map((item) => (
              <span key={item.layer} className="cross-ledger-legend-item">
                <span className="cross-ledger-legend-dot" style={{ background: item.color }} />
                {item.label}
              </span>
            ))}
          </div>
          <EvidenceGraph
            nodes={graphNodes}
            edges={trace.edges || []}
            height={360}
            onNodeClick={onNodeClick}
          />
        </>
      ) : (
        <p className="constitutional-muted">
          Steward view: {trace.nodes?.length || 0} spine nodes across Law, CIT, MIT, EIT, and evidence ledgers.
        </p>
      )}
    </section>
  );
}
