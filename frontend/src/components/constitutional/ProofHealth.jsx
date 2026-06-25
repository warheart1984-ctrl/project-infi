import React from 'react';

export function ProofHealth({ health }) {
  if (!health) return null;

  return (
    <div className="constitutional-panel">
      <h3>Proof Health (PIT)</h3>
      <div className="law-card-metrics">
        <span>avg Φ={Number(health.avg_phi || 0).toFixed(3)}</span>
        <span>avg F={Number(health.avg_fitness || 0).toFixed(3)}</span>
        <span>Θ≥{Number(health.theta_pit || 0).toFixed(2)}</span>
      </div>
      {health.below_threshold?.length ? (
        <div className="cit-warning">PIT-LOW: {health.below_threshold.join(', ')}</div>
      ) : null}
      {health.epoch_commit_blocked ? (
        <div className="cit-danger">PIT-BLOCK: epoch commit blocked until proof fitness recovers.</div>
      ) : null}
    </div>
  );
}
