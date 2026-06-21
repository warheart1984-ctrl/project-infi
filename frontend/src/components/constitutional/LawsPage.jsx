import React from 'react';
import { LawCard } from './LawCard';

export function LawsPage({ laws = [], loading, onSelectLaw }) {
  if (loading) {
    return <div className="constitutional-panel">Loading laws…</div>;
  }

  return (
    <div>
      <h2>Sovereign Laws</h2>
      <div className="constitutional-grid">
        {laws.map((law) => (
          <LawCard key={law.law_id} law={law} onSelect={onSelectLaw} />
        ))}
      </div>
    </div>
  );
}
