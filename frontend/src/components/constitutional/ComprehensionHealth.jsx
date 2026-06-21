import React from 'react';

export function ComprehensionHealth({ health }) {
  if (!health) return null;

  const warnings = health.warnings || [];

  return (
    <div className="constitutional-panel">
      <h3>Comprehension Health</h3>
      <div className="law-card-metrics">
        <span>avg Χ={Number(health.avg_chi || 0).toFixed(3)}</span>
        <span>Θ≥{Number(health.theta_min || 0).toFixed(2)}</span>
        <span>Δ≤{Number(health.delta_max || 0).toFixed(2)}</span>
      </div>
      {health.below_threshold?.length ? (
        <div className="cit-warning">
          CIT-LOW: below threshold — {health.below_threshold.join(', ')}
        </div>
      ) : null}
      {health.drift_detected ? (
        <div className="cit-warning">CIT-DRIFT: comprehension drift detected across recent epochs.</div>
      ) : null}
      {health.epoch_commit_blocked ? (
        <div className="cit-danger">CIT-BLOCK: epoch commit blocked until comprehension recovers.</div>
      ) : null}
      {warnings.slice(0, 4).map((item) => (
        <div key={`${item.code}-${item.object_id}`} className="cit-warning">
          {item.code}: {item.object_type}/{item.object_id}
        </div>
      ))}
    </div>
  );
}
