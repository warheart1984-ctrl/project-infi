import React from 'react';

export function OutcomeHealth({ health, overall }) {
  if (!health) return null;

  return (
    <div className="constitutional-panel">
      <h3>Outcome Variance</h3>
      <div className="law-card-metrics">
        <span>drift={Number(health.outcome_drift || 0).toFixed(3)}</span>
        <span>Θ≤{Number(health.theta_outcome_drift || 0).toFixed(2)}</span>
        {overall != null ? <span>H={Number(overall).toFixed(3)}</span> : null}
      </div>
      {health.concerning_outcomes?.length ? (
        <div className="cit-warning">OIT-CONCERNING: {health.concerning_outcomes.join(', ')}</div>
      ) : null}
      {health.critical_outcomes?.length ? (
        <div className="cit-danger">OIT-CRITICAL: {health.critical_outcomes.join(', ')}</div>
      ) : null}
      {health.epoch_commit_blocked ? (
        <div className="cit-danger">OIT-BLOCK: epoch commit blocked until outcome drift recovers.</div>
      ) : null}
    </div>
  );
}
