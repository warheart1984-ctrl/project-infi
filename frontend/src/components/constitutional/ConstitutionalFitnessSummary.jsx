import React from 'react';

/** Userland aggregate — constitutional fitness summary (CRK-T1). */
export function ConstitutionalFitnessSummary({
  overall,
  epoch,
  lawCount,
  avgFitness,
  blocked,
  blockReasons = [],
}) {
  return (
    <div className="constitutional-panel constitutional-fitness-summary">
      <h3>Constitutional Fitness Summary</h3>
      <p className="constitutional-muted">
        Summary of kernel-level fitness projections over the five CRK-1 objects.
      </p>
      <div className="law-card-metrics">
        <span>H={Number(overall || 0).toFixed(3)}</span>
        <span>Epoch {epoch ?? '—'}</span>
        <span>Laws {lawCount ?? 0}</span>
        <span>avg F={Number(avgFitness || 0).toFixed(3)}</span>
      </div>
      {blocked ? (
        <p className="constitutional-warning">
          Epoch blocked: {(blockReasons.length ? blockReasons : ['SPINE-BLOCK']).join(', ')}
        </p>
      ) : null}
    </div>
  );
}
