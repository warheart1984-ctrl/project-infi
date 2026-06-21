import React from 'react';

export function MeaningStrip({
  mu = 0,
  purpose,
  canonicalMeaning,
  intentNote,
  stewardMode = false,
}) {
  return (
    <section className="meaning-strip">
      <header className="meaning-strip-header">
        <h3>{stewardMode ? 'Steward Meaning' : 'Meaning'}</h3>
        <span className="meaning-score">Μ(X) = {Number(mu).toFixed(3)}</span>
      </header>

      <div className="meaning-grid">
        <div>
          <h4>Purpose</h4>
          <p>{purpose}</p>
        </div>
        <div>
          <h4>Canonical Meaning</h4>
          <p>{canonicalMeaning}</p>
        </div>
        <div>
          <h4>Constitutional Intent</h4>
          <p>{intentNote}</p>
        </div>
      </div>
    </section>
  );
}
