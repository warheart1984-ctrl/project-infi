import React from 'react';

const classificationLabel = {
  acceptable: 'Acceptable',
  concerning: 'Concerning',
  critical: 'Critical',
};

/** Userland projection — outcome variance over OutcomeObject (CRK-T1). */
export function OutcomeVariance({
  outcomeId,
  decisionId,
  epoch,
  varianceClassification,
  varianceDelta,
  expectedSummary,
  observedSummary,
  onReplay,
  onTrace,
}) {
  const cls = `outcome-strip outcome-${varianceClassification || 'acceptable'}`;

  return (
    <section className={cls}>
      <header className="outcome-strip-header">
        <h3>Outcome Variance</h3>
        <p className="constitutional-muted">How reality matched expectations.</p>
        <div className="outcome-meta">
          <span className="outcome-id">OUT {outcomeId}</span>
          <span className="outcome-decision">DEC {decisionId}</span>
          <span className="outcome-epoch">Epoch {epoch}</span>
          <span className={`outcome-class outcome-class-${varianceClassification}`}>
            {classificationLabel[varianceClassification] || varianceClassification}
          </span>
        </div>
      </header>

      <div className="outcome-grid">
        <div>
          <h4>Expected</h4>
          <p>{expectedSummary}</p>
        </div>
        <div>
          <h4>Observed</h4>
          <p>{observedSummary}</p>
        </div>
        <div>
          <h4>Variance</h4>
          <ul className="outcome-variance-list">
            {Object.entries(varianceDelta || {}).map(([key, value]) => (
              <li key={key}>
                <span className="variance-key">{key}</span>
                <span className="variance-value">{Number(value).toFixed(3)}</span>
              </li>
            ))}
          </ul>
        </div>
        <div className="outcome-actions">
          <button
            type="button"
            className="constitutional-btn constitutional-btn-secondary"
            onClick={onTrace}
          >
            Trace
          </button>
          <button
            type="button"
            className="constitutional-btn constitutional-btn-secondary"
            onClick={onReplay}
          >
            Replay
          </button>
        </div>
      </div>
    </section>
  );
}
