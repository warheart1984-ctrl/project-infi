import React from 'react';

export function StructuralHealth({ health }) {
  if (!health) return null;

  return (
    <div className="constitutional-panel">
      <h3>Structural Health (SIT)</h3>
      <div className="law-card-metrics">
        <span>avg Σ={Number(health.avg_sigma || 0).toFixed(3)}</span>
        <span>Θ≥{Number(health.theta_sit || 0).toFixed(2)}</span>
      </div>
      {health.below_threshold?.length ? (
        <div className="cit-warning">SIT-LOW: {health.below_threshold.join(', ')}</div>
      ) : null}
      {health.epoch_commit_blocked ? (
        <div className="cit-danger">SIT-BLOCK: epoch commit blocked until structure recovers.</div>
      ) : null}
    </div>
  );
}
