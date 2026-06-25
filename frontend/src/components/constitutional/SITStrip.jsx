import React from 'react';

export function SITStrip({
  sigma = 0,
  structureSummary,
  recoveryHint,
  operatorIndependence,
  stewardMode = false,
}) {
  return (
    <section className="sit-strip">
      <header className="sit-strip-header">
        <h3>{stewardMode ? 'Steward Structure' : 'Structure'}</h3>
        <span className="sit-score">Σ(S) = {Number(sigma).toFixed(3)}</span>
      </header>
      <div className="sit-grid">
        <div>
          <h4>Structure Summary</h4>
          <p>{structureSummary}</p>
        </div>
        <div>
          <h4>Recovery</h4>
          <p>{recoveryHint}</p>
        </div>
        <div>
          <h4>Operator Independence</h4>
          <p>{operatorIndependence}</p>
        </div>
      </div>
    </section>
  );
}
