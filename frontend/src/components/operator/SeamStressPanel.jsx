import React from 'react';

function toneForClosure(status) {
  return status === 'closed' ? 'aligned' : 'missing';
}

export function SeamStressPanel({ infinity1, liveStress }) {
  const seam = infinity1?.seam_stress || {};
  const health = infinity1?.health || {};
  const live = liveStress || infinity1?.live_stress || {};

  return (
    <section className="workbench-section page-panel" data-testid="infinity1-seam-stress">
      <div className="workbench-section-head">
        <div>
          <span>SEAM_LAW</span>
          <h2>Seam stress</h2>
        </div>
        <span className={`workbench-chip ${toneForClosure(seam.closure_status)}`}>
          {seam.closure_status || 'unknown'}
        </span>
      </div>
      <p className="workbench-muted">
        {seam.total_probes ?? '—'} probes · {seam.failure_count ?? 0} failures · critical/high{' '}
        {seam.critical_high_count ?? 0}
      </p>
      <div className="workbench-chip-row">
        <span className={`workbench-chip ${health.healthy ? 'aligned' : 'missing'}`}>
          health={health.healthy ? 'ok' : 'degraded'}
        </span>
        <span className="workbench-chip aligned">live_err={live.err ?? 0}</span>
        <span className="workbench-chip aligned">routes={seam.route_inventory?.total_routes ?? '—'}</span>
      </div>
      <small className="workbench-muted">
        Last run {seam.generated_at || '—'} · audit {seam.audit_doc || 'docs/audit/SEAM_STRESS_RUN_2026-06-06.md'}
      </small>
    </section>
  );
}
