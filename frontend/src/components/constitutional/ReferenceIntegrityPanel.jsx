import React, { useEffect, useState } from 'react';

function Metric({ label, value }) {
  return (
    <div className="ref-metric">
      <span className="ref-label">{label}</span>
      <span className="ref-value">{Number(value).toFixed(2)}</span>
    </div>
  );
}

export function ReferenceIntegrityPanel() {
  const [metrics, setMetrics] = useState(null);

  useEffect(() => {
    const poll = () => {
      fetch('/api/kernel/reference')
        .then((response) => response.json())
        .then((data) => setMetrics(data))
        .catch(() => {});
    };
    poll();
    const interval = setInterval(poll, 10000);
    return () => clearInterval(interval);
  }, []);

  if (!metrics) {
    return (
      <section className="constitutional-panel reference-panel">
        <h3>Identity / Reference Integrity (CRK-T5)</h3>
        <p className="constitutional-muted">Loading identity alignment metrics…</p>
      </section>
    );
  }

  return (
    <section className="constitutional-panel reference-panel">
      <h3>Identity / Reference Integrity (CRK-T5)</h3>
      <p className="constitutional-muted">Are we still optimizing for the same civilization?</p>
      <div className="ref-summary">
        <span className="ref-label">Reference integrity</span>
        <span className="ref-value ref-value-strong">
          {Number(metrics.reference_integrity ?? 0).toFixed(2)}
        </span>
      </div>
      <div className="ref-grid">
        <Metric label="Mission Drift" value={metrics.mission} />
        <Metric label="Value Drift" value={metrics.values} />
        <Metric label="Invariant Erosion" value={metrics.invariants} />
        <Metric label="Authority Drift" value={metrics.authority} />
        <Metric label="Decision–Identity Divergence" value={metrics.decision} />
        <Metric label="Outcome–Identity Divergence" value={metrics.outcome} />
        <Metric label="Cross-Epoch Inconsistency" value={metrics.epoch} />
      </div>
    </section>
  );
}
