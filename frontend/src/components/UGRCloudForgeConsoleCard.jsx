import React from 'react';

function meshTone(meshHealth) {
  const status = String(meshHealth?.poll_status || '').toLowerCase();
  if (status === 'ok') {
    return 'aligned';
  }
  if (status === 'partial') {
    return 'warning';
  }
  return 'missing';
}

export function UGRCloudForgeConsoleCard({ compact = false, meshHealth = {} }) {
  const services = meshHealth?.services || [];
  const total = meshHealth?.total_count ?? services.length;
  const healthy = meshHealth?.healthy_count ?? services.filter((service) => service.status === 'ok').length;

  return (
    <section className="workbench-section page-panel" data-testid="ugr-cloud-forge-console-card">
      <div className="workbench-section-head">
        <div>
          <span>Cloud Forge</span>
          <h2>{compact ? 'Runtime mesh' : 'UGR Cloud Forge'}</h2>
        </div>
        <span className={`workbench-chip ${meshTone(meshHealth)}`}>
          {meshHealth?.poll_status || 'unknown'}
        </span>
      </div>
      <p className="workbench-muted">
        {healthy}/{total} services healthy · {meshHealth?.polled_at_utc || 'not polled'}
      </p>
      <div className="workbench-chip-row">
        <span className="workbench-chip aligned">advisory</span>
        <span className="workbench-chip warning">read-only</span>
        <span className="workbench-chip aligned">receipts</span>
      </div>
    </section>
  );
}
