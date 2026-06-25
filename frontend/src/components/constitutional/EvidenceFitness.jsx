import React from 'react';

/** Userland projection — EIT evidence fitness over EvidenceObject (CRK-T1). */
export function EvidenceFitness({
  omega,
  components,
  convergence,
  lineageSummary,
  traceLinks,
  stewardMode,
  onTrace,
  onReplay,
}) {
  const conv = convergence || {};
  const status = conv.status || 'ok';

  return (
    <section className="eit-strip">
      <header className="eit-strip-header">
        <h3>Evidence Fitness</h3>
        <p className="constitutional-muted">Provenance and convergence of evidence.</p>
        <span className="eit-score">Ω(E) = {Number(omega || 0).toFixed(3)}</span>
      </header>
      <p className="constitutional-muted">{lineageSummary}</p>
      {!stewardMode && components ? (
        <div className="eit-grid">
          <div>
            <h4>Completeness</h4>
            <p>Q_comp = {Number(components.Q_comp || 0).toFixed(3)}</p>
          </div>
          <div>
            <h4>Validity</h4>
            <p>Q_valid = {Number(components.Q_valid || 0).toFixed(3)}</p>
          </div>
          <div>
            <h4>Robustness</h4>
            <p>Q_rob = {Number(components.Q_rob || 0).toFixed(3)}</p>
          </div>
          <div>
            <h4>Traceability</h4>
            <p>Q_trace = {Number(components.Q_trace || 0).toFixed(3)}</p>
          </div>
          <div>
            <h4>EIT-2 Convergence</h4>
            <p>
              operator {conv.operator_convergent ? '✓' : '✗'} · temporal{' '}
              {conv.temporal_convergent ? '✓' : '✗'} · {status}
            </p>
          </div>
          <div className="cit-actions">
            <button type="button" className="constitutional-btn constitutional-btn-secondary" onClick={onTrace}>
              Trace
            </button>
            <button type="button" className="constitutional-btn constitutional-btn-secondary" onClick={onReplay}>
              Replay
            </button>
          </div>
        </div>
      ) : null}
      {!stewardMode && traceLinks?.length ? (
        <div className="cit-role-badges">
          {traceLinks.map((link) => (
            <span key={`${link.kind}-${link.target}`} className="cit-role-badge">
              {link.label}
            </span>
          ))}
        </div>
      ) : null}
    </section>
  );
}
