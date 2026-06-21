import React from 'react';

export function EvidenceFitnessHealth({ health }) {
  if (!health) return null;

  return (
    <div className="constitutional-panel">
      <h3>Evidence Fitness</h3>
      <div className="law-card-metrics">
        <span>avg Ω={Number(health.avg_omega || 0).toFixed(3)}</span>
        <span>Θ≥{Number(health.theta_evidence || 0).toFixed(2)}</span>
      </div>
      {health.below_threshold?.length ? (
        <div className="cit-warning">EIT-LOW: {health.below_threshold.join(', ')}</div>
      ) : null}
      {health.convergence_detected ? (
        <div className="cit-warning">EIT2: lineage convergence drift detected.</div>
      ) : null}
    </div>
  );
}
