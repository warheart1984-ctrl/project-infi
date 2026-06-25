import React from 'react';

export function PodStrip({
  podId,
  displayName,
  provenCount,
  reputation,
  discoveryCount,
  arcTier,
  rewardMultiplier,
}) {
  const tierLabel = arcTier || 'none';

  return (
    <section className="pod-strip">
      <header className="pod-strip-header">
        <h3>{displayName}</h3>
        <span className="pod-id">{podId}</span>
      </header>

      <div className="pod-grid">
        <div>
          <h4>Discoveries</h4>
          <p>{discoveryCount}</p>
        </div>
        <div>
          <h4>Proven</h4>
          <p>{provenCount}</p>
        </div>
        <div>
          <h4>Reputation</h4>
          <p>{Number(reputation).toLocaleString()}</p>
        </div>
        <div>
          <h4>Arc tier</h4>
          <p>{tierLabel}</p>
        </div>
        <div>
          <h4>Reward multiplier</h4>
          <p>{Number(rewardMultiplier).toFixed(1)}×</p>
        </div>
      </div>
    </section>
  );
}
