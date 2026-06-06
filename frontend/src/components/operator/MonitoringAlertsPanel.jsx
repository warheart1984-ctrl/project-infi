import React from 'react';

export function MonitoringAlertsPanel({ monitoring }) {
  const data = monitoring || {};
  const alerts = data.alerts || [];
  const sentinel = data.operator_health_sentinel?.sentinel || {};
  const rail = data.cloud_forge_rail || {};
  const mesh = data.mesh_poll?.mesh || {};

  return (
    <section className="workbench-section page-panel" data-testid="infinity1-monitoring-alerts">
      <div className="workbench-section-head">
        <div>
          <span>Ops</span>
          <h2>Monitoring alerts</h2>
        </div>
        <span className={`workbench-chip ${data.alert_count ? 'warning' : 'aligned'}`}>
          alerts={data.alert_count ?? 0}
        </span>
      </div>
      <div className="workbench-chip-row">
        <span className="workbench-chip aligned">
          sentinel={sentinel.verification_status || '—'}
        </span>
        <span className="workbench-chip aligned">
          rail_records={rail.record_count ?? 0}
        </span>
        <span className={`workbench-chip ${(mesh.healthy_count ?? 0) < (mesh.total_count ?? 0) ? 'warning' : 'aligned'}`}>
          mesh={mesh.healthy_count ?? 0}/{mesh.total_count ?? 0}
        </span>
      </div>
      <div className="workbench-history-list">
        {alerts.length === 0 ? (
          <div className="workbench-history-item">
            <p className="workbench-muted">No open advisory alerts.</p>
          </div>
        ) : (
          alerts.map((alert) => (
            <div key={alert.id} className="workbench-history-item">
              <div className="workbench-list-title">
                <strong>{alert.id}</strong>
                <span className="workbench-chip warning">{alert.severity}</span>
              </div>
              <p>{alert.summary}</p>
            </div>
          ))
        )}
      </div>
    </section>
  );
}
