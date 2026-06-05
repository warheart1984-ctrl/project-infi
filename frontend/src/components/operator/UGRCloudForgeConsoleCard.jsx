import React from 'react';

export function UGRCloudForgeConsoleCard({ compact = false, meshHealth = null }) {
  const healthy = meshHealth?.healthy_count ?? 0;
  const total = meshHealth?.total_count ?? 0;

  return (
    <section
      className={`workbench-section page-panel ${compact ? 'operator-console-card--compact' : ''}`}
      data-testid="ugr-cloud-forge-console-card"
    >
      <div className="workbench-section-head">
        <div>
          <span>UGR / Forge</span>
          <h2>Cloud console</h2>
        </div>
      </div>
      <p className="workbench-muted">
        Mesh health {healthy}/{total || '—'} · poll {meshHealth?.poll_status || 'unknown'}
      </p>
    </section>
  );
}
