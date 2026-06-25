import React from 'react';

export function PITStrip({
  phi = 0,
  fitnessCurrent = 0,
  selectionNote,
  evidenceCoupling,
  consensusNote,
  stewardMode = false,
}) {
  return (
    <section className="pit-strip">
      <header className="pit-strip-header">
        <h3>{stewardMode ? 'Steward Proof Fitness' : 'Proof Fitness'}</h3>
        <span className="pit-score">Φ(G) = {Number(phi).toFixed(3)} · F={Number(fitnessCurrent).toFixed(3)}</span>
      </header>
      <div className="pit-grid">
        <div>
          <h4>Selection</h4>
          <p>{selectionNote}</p>
        </div>
        <div>
          <h4>Evidence Coupling</h4>
          <p>{evidenceCoupling}</p>
        </div>
        <div>
          <h4>Consensus</h4>
          <p>{consensusNote}</p>
        </div>
      </div>
    </section>
  );
}
