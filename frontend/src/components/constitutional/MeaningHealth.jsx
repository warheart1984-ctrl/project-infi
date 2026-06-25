import React from 'react';

export function MeaningHealth({ health }) {
  if (!health) return null;

  return (
    <div className="constitutional-panel">
      <h3>Meaning Fitness</h3>
      <div className="law-card-metrics">
        <span>avg Μ={Number(health.avg_mu || 0).toFixed(3)}</span>
        <span>Θ≥{Number(health.theta_mit || 0).toFixed(2)}</span>
      </div>
      {health.below_threshold?.length ? (
        <div className="cit-warning">MIT-LOW: {health.below_threshold.join(', ')}</div>
      ) : null}
    </div>
  );
}
