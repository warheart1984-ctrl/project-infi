import React from 'react';

/** Userland projection — CIT comprehension fitness over kernel objects (CRK-T1). */
export function ComprehensionFitness({
  explain,
  summarize,
  whyExists,
  whatBreaksIfRemoved,
  constitutionalRole = [],
  onTrace,
  onReplay,
  chi = 0,
  traceLinks = [],
  stewardMode = false,
}) {
  return (
    <section className="cit-strip">
      <header className="cit-strip-header">
        <h3>{stewardMode ? 'Steward Comprehension Fitness' : 'Comprehension Fitness'}</h3>
        <p className="constitutional-muted">How well operators can explain this object.</p>
        <span className="cit-score">Χ(X) = {Number(chi).toFixed(3)}</span>
      </header>

      <div className="cit-grid">
        <div>
          <h4>Explain</h4>
          <p>{explain}</p>
        </div>
        <div>
          <h4>Summarize</h4>
          <p>{summarize}</p>
        </div>
        <div>
          <h4>Why It Exists</h4>
          <p>{whyExists}</p>
        </div>
        <div>
          <h4>What Breaks If Removed</h4>
          <p>{whatBreaksIfRemoved}</p>
        </div>
        <div>
          <h4>Constitutional Role</h4>
          <div className="cit-role-badges">
            {constitutionalRole.map((role) => (
              <span key={role} className="cit-role-badge">
                {role}
              </span>
            ))}
          </div>
        </div>
        {!stewardMode ? (
          <div className="cit-actions">
            <button type="button" className="constitutional-btn constitutional-btn-secondary" onClick={onTrace}>
              Trace
            </button>
            <button type="button" className="constitutional-btn constitutional-btn-secondary" onClick={onReplay}>
              Replay
            </button>
          </div>
        ) : null}
      </div>

      {traceLinks?.length ? (
        <div style={{ marginTop: 12 }}>
          <h4>Trace Links</h4>
          <ul className="constitutional-muted">
            {traceLinks.map((link) => (
              <li key={`${link.kind}-${link.target}`}>{link.label || link.target}</li>
            ))}
          </ul>
        </div>
      ) : null}
    </section>
  );
}
