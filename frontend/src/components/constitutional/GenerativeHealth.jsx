import React from 'react';

export function GenerativeHealth({ health }) {
  if (!health) return null;

  return (
    <div className="constitutional-panel">
      <h3>Generative Health (GIT)</h3>
      <div className="law-card-metrics">
        <span>avg Λ={Number(health.avg_lambda || 0).toFixed(3)}</span>
        <span>Θ≥{Number(health.theta_git || 0).toFixed(2)}</span>
      </div>
      {health.below_threshold?.length ? (
        <div className="cit-warning">GIT-LOW: {health.below_threshold.join(', ')}</div>
      ) : null}
      {health.epoch_commit_blocked ? (
        <div className="cit-danger">GIT-BLOCK: epoch commit blocked until generative recovery converges.</div>
      ) : null}
    </div>
  );
}
