import React from 'react';

export function GITStrip({
  lambdaValue = 0,
  generativeLaw,
  crossOperatorNote,
  recoverySummary,
  stewardMode = false,
}) {
  return (
    <section className="git-strip">
      <header className="git-strip-header">
        <h3>{stewardMode ? 'Steward Generative Law' : 'Generative Law'}</h3>
        <span className="git-score">Λ(G) = {Number(lambdaValue).toFixed(3)}</span>
      </header>
      <div className="git-grid">
        <div>
          <h4>Recovered Law</h4>
          <p>{generativeLaw}</p>
        </div>
        <div>
          <h4>Cross-Operator</h4>
          <p>{crossOperatorNote}</p>
        </div>
        <div>
          <h4>Recovery Summary</h4>
          <p>{recoverySummary}</p>
        </div>
      </div>
    </section>
  );
}
